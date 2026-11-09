// Comportamentos da página. Sem este script tudo continua funcionando;
// ele só deixa o formulário mais limpo e pede confirmação antes de excluir.
// Autor: Antonio Santos

document.addEventListener("DOMContentLoaded", () => {
  // No cadastro, mostra só o campo do tipo escolhido (placa ou limite de velocidade)
  const form = document.getElementById("form-veiculo");
  if (form) {
    const atualizar = () => {
      const tipo = form.querySelector("input[name=tipo]:checked")?.value;
      form.querySelectorAll("[data-tipo]").forEach((bloco) => {
        const visivel = bloco.dataset.tipo === tipo;
        bloco.hidden = !visivel;
        bloco.querySelectorAll("input").forEach((campo) => { campo.required = visivel; });
      });
    };
    form.querySelectorAll("input[name=tipo]").forEach((r) => r.addEventListener("change", atualizar));
    atualizar();
  }

  // Confirmação antes de ações que apagam dados
  document.querySelectorAll("form[data-confirmar]").forEach((f) => {
    f.addEventListener("submit", (evento) => {
      if (!confirm(f.dataset.confirmar)) evento.preventDefault();
    });
  });

  // Evita gravar duas vezes com um clique duplo: depois do envio, o botão fica desativado
  document.querySelectorAll("form[method=post]").forEach((f) => {
    f.addEventListener("submit", (evento) => {
      if (evento.defaultPrevented) return;
      f.querySelectorAll("button").forEach((botao) => { botao.disabled = true; });
    });
  });
});
