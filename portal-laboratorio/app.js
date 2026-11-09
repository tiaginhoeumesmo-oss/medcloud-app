// Configuração Supabase (Usando a chave anônima publicável e proxy Vercel para estabilidade de rede)
let supabaseUrl = 'https://wkmbkipygdjinlezlftt.supabase.co';

// Se estiver em produção (não-local), usa o proxy da Vercel para evitar bloqueios de provedores/firewalls
if (window.location.protocol.startsWith('http') && window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
    supabaseUrl = window.location.origin + '/supabase';
}

const supabaseKey = 'sb_publishable__ArqbbdwN_zbCqkrRDcPXA_ZEKrmwYV';
let supabaseClient = null;

try {
    if (window.supabase && window.supabase.createClient) {
        supabaseClient = window.supabase.createClient(supabaseUrl, supabaseKey);
    } else {
        console.warn("SDK do Supabase não carregado. Verifique a conexão com a internet.");
    }
} catch (e) {
    console.error("Erro ao inicializar Supabase:", e);
}

// Utilitário para exibir mensagens de status
function showStatus(message, type = 'loading') {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.className = ''; // Reset classes
    
    let icon = '';
    if (type === 'error') {
        icon = '<i class="ph ph-warning-circle"></i>';
        statusDiv.classList.add('status-error');
    } else if (type === 'success') {
        icon = '<i class="ph ph-check-circle"></i>';
        statusDiv.classList.add('status-success');
    } else if (type === 'ai') {
        icon = '<i class="ph ph-brain ph-spin"></i>';
        statusDiv.classList.add('ai-processing');
    } else {
        icon = '<i class="ph ph-spinner-gap ph-spin"></i>';
        statusDiv.classList.add('status-loading');
    }

    statusDiv.innerHTML = `${icon} <span>${message}</span>`;
    statusDiv.style.display = 'block';
}

function clearStatus() {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.innerHTML = '';
    statusDiv.className = '';
    statusDiv.style.display = 'none';
}

// Funções de Autenticação (Mock Seguro Básico)
window.fazerLogin = function () {
    const user = document.getElementById('userLogin').value.trim().toLowerCase();
    const pass = document.getElementById('passLogin').value.trim();

    // Verificação simples usando base64 para evitar credenciais em texto puro no código
    // admin = YWRtaW4= | 1234 = MTIzNA==
    if (btoa(user) === 'YWRtaW4=' && btoa(pass) === 'MTIzNA==') {
        const loginScreen = document.getElementById('loginScreen');
        const dashboardScreen = document.getElementById('dashboardScreen');
        
        loginScreen.classList.add('fade-out');
        
        setTimeout(() => {
            loginScreen.style.display = 'none';
            dashboardScreen.style.display = 'block';
            setTimeout(() => dashboardScreen.classList.add('fade-in'), 50);
            window.alternarPaineis();
        }, 400);
    } else {
        alert("Credenciais incorretas! (Dica: admin / 1234)");
    }
}

window.sair = function () {
    const loginScreen = document.getElementById('loginScreen');
    const dashboardScreen = document.getElementById('dashboardScreen');
    
    dashboardScreen.classList.remove('fade-in');
    dashboardScreen.classList.add('fade-out');
    
    setTimeout(() => {
        dashboardScreen.style.display = 'none';
        dashboardScreen.classList.remove('fade-out');
        
        loginScreen.style.display = 'block';
        setTimeout(() => {
            loginScreen.classList.remove('fade-out');
            loginScreen.classList.add('fade-in');
        }, 50);
        
        // Limpar inputs
        document.getElementById('userLogin').value = '';
        document.getElementById('passLogin').value = '';
    }, 400);
}

// Alternância de UI baseada na categoria
window.alternarPaineis = function () {
    const cat = document.getElementById('category').value;
    
    const panels = ['boxLaboratorio', 'boxImagem', 'boxOutros'];
    panels.forEach(p => document.getElementById(p).classList.remove('active'));

    if (cat === 'Laboratoriais') {
        document.getElementById('boxLaboratorio').classList.add('active');
    } else if (cat === 'Imagem') {
        document.getElementById('boxImagem').classList.add('active');
    } else {
        document.getElementById('boxOutros').classList.add('active');
    }
}

// Atualização de nome do arquivo no input customizado
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    
    if(fileInput && fileNameDisplay) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                fileNameDisplay.textContent = e.target.files[0].name;
            } else {
                fileNameDisplay.textContent = 'Clique para anexar PDF';
            }
        });
    }
    
    // Suporte a "Enter" no login
    document.getElementById('passLogin')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') window.fazerLogin();
    });
});

// Fluxo principal de envio
window.sendFile = async function () {
    const btn = document.getElementById('sendBtn');
    let patientId = document.getElementById('patientId').value.trim();
    const category = document.getElementById('category').value;
    const file = document.getElementById('fileInput').files[0];

    if (!file) {
        showStatus('Anexe o laudo PDF.', 'error');
        return;
    }
    if (!supabaseClient) {
        showStatus('Conexão com o banco de dados offline. Verifique a internet.', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="ph ph-spinner-gap ph-spin"></i> Processando...';
    clearStatus();

    try {
        let payloadJSON = [];
        let usouIA = false;
        let requiresIA = false;

        // Captura de valores preenchidos manualmente
        const valHemo = document.getElementById('valHemo') ? document.getElementById('valHemo').value : '';
        const valLeuco = document.getElementById('valLeuco') ? document.getElementById('valLeuco').value : '';
        const valGlico = document.getElementById('valGlico') ? document.getElementById('valGlico').value : '';
        const valPota = document.getElementById('valPota') ? document.getElementById('valPota').value : '';
        const inputsPreenchidos = valHemo || valLeuco || valGlico || valPota;
        const pacsUrl = document.getElementById('pacsLink') ? document.getElementById('pacsLink').value.trim() : '';

        // Condições para acionar o motor de inteligência artificial
        if (!patientId) requiresIA = true;
        if (category === 'Laboratoriais' && !inputsPreenchidos) requiresIA = true;
        if (category === 'Imagem' && !pacsUrl) requiresIA = true;

        if (requiresIA) {
            usouIA = true;
            showStatus('Lendo e extraindo dados do PDF...', 'ai');
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const apiResponse = await fetch('/api/process-pdf', {
                    method: 'POST',
                    body: formData
                });
                
                if (!apiResponse.ok) {
                    throw new Error("Erro na comunicação com o servidor de IA (Status " + apiResponse.status + ")");
                }
                
                const extractedData = await apiResponse.json();

                // 1. Preencher ID do Paciente automaticamente
                if (!patientId && extractedData.patientId) {
                    patientId = extractedData.patientId;
                    document.getElementById('patientId').value = patientId; // Mostra na tela pro usuário
                }

                const unidades = {
                    "Hemoglobina": "g/dL", "Hematócrito": "%", "Leucócitos": "/mm³", "Linfócitos": "/mm³", "Plaquetas": "/mm³",
                    "Glicose": "mg/dL", "Potássio": "mEq/L", "Sódio": "mEq/L", "Creatinina": "mg/dL", "Ureia": "mg/dL",
                    "Colesterol Total": "mg/dL", "Colesterol HDL": "mg/dL", "Colesterol LDL": "mg/dL", "Triglicerídeos": "mg/dL",
                    "Ácido Úrico": "mg/dL", "TSH": "µUI/mL", "T4 Livre": "ng/dL"
                };

                // 2. Extrair Dados Clínicos e Credenciais
                if (extractedData.dadosClinicos) {
                    extractedData.dadosClinicos.forEach(dado => {
                        if (category === 'Laboratoriais' && (dado.tipo === 'lab' || dado.nome !== 'Acesso PACS')) {
                            payloadJSON.push({
                                nome: dado.nome,
                                valor: typeof dado.valor === 'string' ? parseFloat(dado.valor) : dado.valor,
                                uni: dado.uni || unidades[dado.nome] || "",
                                ref: ""
                            });
                        } else if (category === 'Imagem' && dado.tipo === 'pacs') {
                            payloadJSON.push({
                                tipo: 'pacs',
                                usuario: dado.usuario || "",
                                senha: dado.senha || "",
                                url: dado.url || pacsUrl || ""
                            });
                        }
                    });
                }
                
                if (category === 'Laboratoriais' && payloadJSON.length === 0) {
                     console.warn("Nenhum dado numérico identificado no PDF.");
                }
            } catch (apiError) {
                console.error("Falha ao extrair dados:", apiError);
                if (!patientId) {
                    throw new Error("A IA falhou e não foi possível identificar o ID do paciente automaticamente. Preencha-o manualmente.");
                } else {
                    showStatus("Aviso: Falha na IA. Enviando documento sem extração.", "loading");
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
        }

        // Validação vital: sem o patientId, o banco de dados recusa a inserção.
        if (!patientId) {
            throw new Error("Não foi possível encontrar a numeração de 'ID do Paciente' no PDF. Por favor, digite manualmente.");
        }

        // Fallbacks (se o usuário preencheu e a IA não usou/não encontrou)
        if (category === 'Laboratoriais' && inputsPreenchidos && payloadJSON.length === 0) {
            const addDado = (val, nome, uni, ref) => {
                if (val) payloadJSON.push({ nome, valor: parseFloat(val), uni, ref });
            };
            addDado(valHemo, 'Hemoglobina', 'g/dL', '12 - 17');
            addDado(valLeuco, 'Leucócitos', '/mm³', '4000 - 11000');
            addDado(valGlico, 'Glicose', 'mg/dL', '70 - 99');
            addDado(valPota, 'Potássio', 'mEq/L', '3.5 - 5.1');
        } else if (category === 'Imagem' && pacsUrl && payloadJSON.length === 0) {
            payloadJSON = [{ tipo: 'pacs', url: pacsUrl }];
        }

        showStatus('Salvando documento de forma segura...', 'loading');
        
        const nomeLimpo = file.name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9.]/g, '_');
        const fileName = `${Date.now()}_${nomeLimpo}`;
        
        // Upload do arquivo
        const { error: uploadError } = await supabaseClient.storage.from('laudos').upload(fileName, file);
        if (uploadError) throw new Error("Erro ao fazer upload: " + uploadError.message);
        
        const { data: urlData } = supabaseClient.storage.from('laudos').getPublicUrl(fileName);

        // Salvar no banco de dados
        const { error: dbError } = await supabaseClient
            .from('exames')
            .insert([{
                paciente_id: patientId,
                url_laudo: urlData.publicUrl,
                categoria: category,
                nome_arquivo: file.name,
                dados_estruturados: payloadJSON
            }]);

        if (dbError) throw dbError;

        // Sucesso
        const successMsg = usouIA 
            ? 'Transmitido e processado pelo servidor com sucesso!' 
            : 'Transmitido com sucesso!';
        showStatus(successMsg, 'success');

        // Limpar formulário
        document.getElementById('fileInput').value = '';
        document.getElementById('fileNameDisplay').textContent = 'Clique para anexar PDF';
        document.getElementById('patientId').value = '';
        
        document.querySelectorAll('.json-item input').forEach(i => i.value = '');
        if (document.getElementById('pacsLink')) document.getElementById('pacsLink').value = '';
        
        // Esconder mensagem de sucesso após alguns segundos
        setTimeout(() => clearStatus(), 5000);

    } catch (error) {
        showStatus(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="ph ph-paper-plane-tilt"></i> Enviar e Processar';
    }
}
