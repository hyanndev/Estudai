const elementos = {
  materiais: document.getElementById("materiais"),
  resumo: document.getElementById("resumo-materiais"),
  lista: document.getElementById("lista-materiais"),
  areaEnvio: document.getElementById("area-envio"),
  arquivo: document.getElementById("arquivo"),
  limites: document.getElementById("limites"),
  statusEnvio: document.getElementById("status-envio"),
  avisoSessao: document.getElementById("aviso-sessao"),
  vazio: document.getElementById("vazio"),
  textoVazio: document.getElementById("texto-vazio"),
  sugestoes: document.getElementById("sugestoes"),
  mensagens: document.getElementById("mensagens"),
  formulario: document.getElementById("formulario"),
  pergunta: document.getElementById("pergunta"),
  enviar: document.getElementById("enviar"),
  contagem: document.getElementById("contagem"),
};

const estado = {
  materiais: [],
  limites: { arquivos: 6, tamanho_mb: 2 },
  ocupado: false,
};

const telaLarga = window.matchMedia("(min-width: 56rem)");

function ajustarPainel() {
  if (telaLarga.matches) {
    elementos.materiais.open = true;
  }
}
telaLarga.addEventListener("change", ajustarPainel);
ajustarPainel();
if (!telaLarga.matches) {
  elementos.materiais.open = false;
}

async function chamar(caminho, opcoes) {
  try {
    const resposta = await fetch(caminho, opcoes);
    let dados = null;
    try {
      dados = await resposta.json();
    } catch (e) {
      dados = null;
    }
    return { ok: resposta.ok, status: resposta.status, dados };
  } catch (e) {
    return { ok: false, status: 0, dados: null };
  }
}

function textoDoErro(resultado, padrao) {
  if (resultado.status === 0) {
    return "Não foi possível conectar. Confira sua internet e tente de novo.";
  }
  const detalhe = resultado.dados && resultado.dados.detail;
  if (typeof detalhe === "string") {
    return detalhe;
  }
  if (resultado.status === 422) {
    return "Confira os dados enviados e tente de novo.";
  }
  if (resultado.status === 429) {
    return "Muitas tentativas em pouco tempo. Aguarde um minuto e tente de novo.";
  }
  if (resultado.status === 503) {
    return "O serviço está indisponível no momento. Tente de novo em instantes.";
  }
  return padrao;
}

function aplicarMateriais(dados) {
  estado.materiais = dados.materiais;
  if (dados.limites) {
    estado.limites = dados.limites;
  }
  desenharMateriais();
}

function desenharMateriais() {
  const enviados = estado.materiais.filter((m) => !m.exemplo).length;
  elementos.resumo.textContent = `${estado.materiais.length} ${estado.materiais.length === 1 ? "arquivo" : "arquivos"}`;
  elementos.limites.textContent = `Até ${estado.limites.arquivos} arquivos seus (${enviados} enviados), ${estado.limites.tamanho_mb} MB cada.`;
  elementos.lista.replaceChildren();
  if (estado.materiais.length === 0) {
    const vazio = document.createElement("li");
    vazio.className = "vazio-lista";
    vazio.textContent = "Nenhum material ainda. Adicione um arquivo para começar.";
    elementos.lista.appendChild(vazio);
  }
  for (const material of estado.materiais) {
    const item = document.createElement("li");
    item.className = "material";

    const info = document.createElement("div");
    info.className = "material-info";
    const nome = document.createElement("span");
    nome.className = "material-nome";
    nome.textContent = material.nome;
    if (material.exemplo) {
      const selo = document.createElement("span");
      selo.className = "selo";
      selo.textContent = "exemplo";
      nome.appendChild(selo);
    }
    const meta = document.createElement("span");
    meta.className = "material-meta";
    meta.textContent = `${material.trechos} ${material.trechos === 1 ? "trecho" : "trechos"}`;
    info.append(nome, meta);

    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "remover";
    botao.textContent = "×";
    botao.setAttribute("aria-label", `Remover ${material.nome}`);
    botao.addEventListener("click", () => removerMaterial(material.nome));

    item.append(info, botao);
    elementos.lista.appendChild(item);
  }
  if (estado.materiais.length === 0 && !telaLarga.matches) {
    elementos.materiais.open = true;
  }
  const temExemplo = estado.materiais.some((m) => m.exemplo);
  elementos.sugestoes.hidden = !temExemplo;
  elementos.textoVazio.textContent = estado.materiais.length === 0
    ? "Adicione um material ao lado para começar. Cada resposta mostra o trecho de onde saiu."
    : "Escreva uma dúvida sobre os seus materiais. Cada resposta mostra o trecho de onde saiu.";
}

async function carregarMateriais(verificarSessao) {
  const antes = estado.materiais.filter((m) => !m.exemplo).map((m) => m.nome);
  const resultado = await chamar("/materiais");
  if (!resultado.ok) {
    return;
  }
  aplicarMateriais(resultado.dados);
  if (verificarSessao) {
    const agora = new Set(estado.materiais.map((m) => m.nome));
    if (antes.some((nome) => !agora.has(nome))) {
      elementos.avisoSessao.textContent = "Sua sessão expirou e os arquivos que você enviou foram apagados. Envie-os de novo se precisar.";
      elementos.avisoSessao.hidden = false;
    }
  }
}

async function removerMaterial(nome) {
  elementos.avisoSessao.hidden = true;
  const resultado = await chamar(`/materiais/${encodeURIComponent(nome)}`, { method: "DELETE" });
  if (resultado.ok) {
    aplicarMateriais(resultado.dados);
  } else if (resultado.status === 404) {
    await carregarMateriais(false);
  } else {
    mostrarStatusEnvio([], textoDoErro(resultado, "Não foi possível remover o arquivo."));
  }
}

function mostrarStatusEnvio(linhas, erro) {
  elementos.statusEnvio.replaceChildren();
  for (const linha of linhas) {
    const p = document.createElement("div");
    p.textContent = linha;
    elementos.statusEnvio.appendChild(p);
  }
  if (erro) {
    const p = document.createElement("div");
    p.className = "linha-erro";
    p.textContent = erro;
    elementos.statusEnvio.appendChild(p);
  }
}

async function enviarArquivos(arquivos) {
  const lista = Array.from(arquivos);
  if (lista.length === 0) {
    return;
  }
  elementos.avisoSessao.hidden = true;
  const erros = [];
  for (const arquivo of lista) {
    mostrarStatusEnvio([`Processando ${arquivo.name}…`], "");
    const dadosForm = new FormData();
    dadosForm.append("arquivo", arquivo);
    const resultado = await chamar("/materiais", { method: "POST", body: dadosForm });
    if (resultado.ok) {
      aplicarMateriais(resultado.dados);
    } else {
      erros.push(`${arquivo.name}: ${textoDoErro(resultado, "não foi possível enviar.")}`);
    }
  }
  elementos.statusEnvio.replaceChildren();
  for (const erro of erros) {
    const p = document.createElement("div");
    p.className = "linha-erro";
    p.textContent = erro;
    elementos.statusEnvio.appendChild(p);
  }
  if (erros.length === 0) {
    const ok = document.createElement("div");
    ok.textContent = lista.length === 1 ? "Material adicionado." : "Materiais adicionados.";
    elementos.statusEnvio.appendChild(ok);
  }
  elementos.arquivo.value = "";
}

elementos.arquivo.addEventListener("change", () => enviarArquivos(elementos.arquivo.files));

for (const tipo of ["dragenter", "dragover"]) {
  elementos.areaEnvio.addEventListener(tipo, (evento) => {
    evento.preventDefault();
    elementos.areaEnvio.classList.add("arrastando");
  });
}
for (const tipo of ["dragleave", "drop"]) {
  elementos.areaEnvio.addEventListener(tipo, (evento) => {
    evento.preventDefault();
    elementos.areaEnvio.classList.remove("arrastando");
  });
}
elementos.areaEnvio.addEventListener("drop", (evento) => enviarArquivos(evento.dataTransfer.files));

function criarMensagem(texto) {
  const item = document.createElement("li");
  const pergunta = document.createElement("div");
  pergunta.className = "pergunta-feita";
  pergunta.textContent = texto;
  const resposta = document.createElement("div");
  resposta.className = "resposta carregando";
  const corpo = document.createElement("p");
  corpo.className = "texto-resposta";
  corpo.textContent = "Procurando nos seus materiais…";
  resposta.appendChild(corpo);
  item.append(pergunta, resposta);
  elementos.mensagens.appendChild(item);
  elementos.vazio.hidden = true;
  item.scrollIntoView({ block: "nearest", behavior: "smooth" });
  return { resposta, corpo };
}

function preencherFontes(resposta, fontes) {
  if (!fontes || fontes.length === 0) {
    return;
  }
  const bloco = document.createElement("div");
  bloco.className = "fontes";
  const titulo = document.createElement("p");
  titulo.className = "fontes-titulo";
  titulo.textContent = "De onde veio";
  bloco.appendChild(titulo);
  for (const fonte of fontes) {
    const detalhes = document.createElement("details");
    detalhes.className = "fonte";
    const resumo = document.createElement("summary");
    const nome = document.createElement("span");
    nome.className = "fonte-nome";
    nome.textContent = fonte.fonte;
    const trecho = document.createElement("span");
    trecho.className = "fonte-trecho";
    trecho.textContent = `trecho ${fonte.trecho}`;
    resumo.append(nome, trecho);
    detalhes.appendChild(resumo);
    if (fonte.texto) {
      const passagem = document.createElement("blockquote");
      passagem.className = "passagem";
      passagem.textContent = fonte.texto;
      detalhes.appendChild(passagem);
    }
    bloco.appendChild(detalhes);
  }
  resposta.appendChild(bloco);
}

async function perguntar(texto) {
  if (estado.ocupado) {
    return;
  }
  const pergunta = texto.trim();
  if (pergunta.length < 3) {
    return;
  }
  estado.ocupado = true;
  elementos.enviar.disabled = true;
  const { resposta, corpo } = criarMensagem(pergunta);
  elementos.pergunta.value = "";
  ajustarAltura();
  const resultado = await chamar("/perguntar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto: pergunta }),
  });
  resposta.classList.remove("carregando");
  if (resultado.ok) {
    corpo.textContent = resultado.dados.resposta;
    if (!resultado.dados.fontes || resultado.dados.fontes.length === 0) {
      resposta.classList.add("sem-resposta");
    }
    preencherFontes(resposta, resultado.dados.fontes);
  } else {
    resposta.classList.add("erro");
    corpo.textContent = textoDoErro(resultado, "Algo deu errado. Tente de novo.");
  }
  estado.ocupado = false;
  elementos.enviar.disabled = false;
  elementos.pergunta.focus({ preventScroll: true });
  carregarMateriais(true);
}

function ajustarAltura() {
  elementos.pergunta.style.height = "auto";
  elementos.pergunta.style.height = `${Math.min(elementos.pergunta.scrollHeight, 160)}px`;
  const tamanho = elementos.pergunta.value.length;
  elementos.contagem.textContent = tamanho > 400 ? `${tamanho} de 500 letras` : "";
}

elementos.formulario.addEventListener("submit", (evento) => {
  evento.preventDefault();
  perguntar(elementos.pergunta.value);
});

elementos.pergunta.addEventListener("input", ajustarAltura);

elementos.pergunta.addEventListener("keydown", (evento) => {
  if (evento.key === "Enter" && !evento.shiftKey && !evento.isComposing) {
    evento.preventDefault();
    perguntar(elementos.pergunta.value);
  }
});

for (const botao of document.querySelectorAll(".sugestao")) {
  botao.addEventListener("click", () => perguntar(botao.textContent));
}

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    carregarMateriais(true);
  }
});

carregarMateriais(false);