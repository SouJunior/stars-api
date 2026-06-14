# Autenticação da API

Este documento descreve o fluxo de autenticação da API Stars, que utiliza o padrão **OAuth2 com Password Flow** e tokens **JWT (JSON Web Token)**.

## Visão Geral

Para acessar as rotas protegidas da API, o frontend deve primeiro autenticar o usuário para obter um `access_token`. Este token deve ser enviado no cabeçalho de todas as requisições subsequentes que exigem autenticação.

## 1. Realizar Login (Obter Token)

O login é feito através do endpoint `/token`. Este endpoint espera que os dados sejam enviados como **Form Data** (`application/x-www-form-urlencoded`), seguindo a especificação OAuth2.

### Endpoint

`POST /token`

### Parâmetros da Requisição (Form Data)

| Campo      | Tipo   | Obrigatório | Descrição                                      |
| :--------- | :----- | :---------- | :--------------------------------------------- |
| `username` | String | Sim         | O e-mail do usuário.                           |
| `password` | String | Sim         | A senha do usuário.                            |
| `scope`    | String | Não         | Escopos de permissão (não utilizado no momento).|

### Exemplo de Requisição (cURL)

```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=usuario@exemplo.com&password=minhasenha123"
```

### Exemplo de Requisição (JavaScript/Fetch)

```javascript
const formData = new URLSearchParams();
formData.append('username', 'usuario@exemplo.com');
formData.append('password', 'minhasenha123');

fetch('http://localhost:8000/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Resposta de Sucesso (200 OK)

A API retornará um objeto JSON contendo o token de acesso e o tipo do token.

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Resposta de Erro (401 Unauthorized)

Se as credenciais estiverem incorretas.

```json
{
  "detail": "Incorrect username or password"
}
```

---

## 2. Acessar Rotas Protegidas

Para acessar endpoints protegidos (ex: `/users/me`, `/users/`), você deve incluir o token recebido no cabeçalho `Authorization` da requisição HTTP.

O formato do cabeçalho deve ser: `Bearer <access_token>`

### Cabeçalho

```text
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Exemplo de Requisição (cURL)

```bash
curl -X GET "http://localhost:8000/users/me/" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Exemplo de Requisição (JavaScript/Fetch)

```javascript
const token = "SEU_ACCESS_TOKEN_AQUI";

fetch('http://localhost:8000/users/me/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

## 3. Tratamento de Erros no Frontend

Ao integrar com o frontend, recomenda-se tratar os seguintes cenários:

*   **401 Unauthorized:** O token é inválido ou expirou.
    *   *Ação sugerida:* Redirecionar o usuário para a tela de login e limpar o token armazenado.
*   **400 Bad Request (Inactive user):** O usuário autenticou, mas a conta está inativa.
    *   *Ação sugerida:* Exibir mensagem informando que a conta está inativa.

## Resumo para Implementação

1.  Crie um formulário de login que envie `username` (email) e `password` para `POST /token`.
2.  Receba o `access_token` e armazene-o de forma segura (ex: Secure Cookie ou LocalStorage).
3.  Configure seu cliente HTTP (Axios, Fetch, etc.) para interceptar requisições e adicionar o header `Authorization: Bearer ...`.
4.  Interceptar respostas `401` para deslogar o usuário automaticamente.
