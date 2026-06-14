# Guia de Integração: Status de Voluntários

Este documento descreve as alterações e novos endpoints adicionados à API para gerenciar o **status dos voluntários** e seu **histórico de alterações**.

## Visão Geral

Agora, cada voluntário possui um `status` atual (ex: "INTERESTED", "ACTIVE", "INACTIVE").
Além disso, toda vez que o status de um voluntário é alterado, um registro é criado no `status_history`, permitindo rastrear a evolução do voluntário no processo.

### Status Padrões
O sistema já vem com os seguintes status pré-definidos:
1.  **INTERESTED**: Status inicial padrão quando um voluntário se cadastra.
2.  **CONTACTED**
3.  **SCREENING**
4.  **ACTIVE**
5.  **INACTIVE**

---

## Alterações nos Modelos de Dados

### Objeto `Volunteer` (Atualizado)
O objeto de voluntário retornado pela API agora inclui campos de status.

```json
{
  "id": 1,
  "name": "João Silva",
  "email": "joao@example.com",
  "linkedin": "...",
  "jobtitle_id": 2,
  "status_id": 1,
  "status": {
    "id": 1,
    "name": "INTERESTED",
    "description": "Volunteer expressed interest."
  },
  "status_history": [
    {
      "id": 1,
      "status_id": 1,
      "created_at": "2023-10-27T10:00:00Z",
      "status": {
        "id": 1,
        "name": "INTERESTED",
        "description": "Volunteer expressed interest."
      }
    }
  ]
}
```

---

## Novos Endpoints e Funcionalidades

### 1. Listar Status Disponíveis
Use este endpoint para popular dropdowns ou filtros no frontend.

- **Método:** `GET`
- **Endpoint:** `/volunteer-statuses/`
- **Exemplo de Resposta:**
  ```json
  [
    {
      "id": 1,
      "name": "INTERESTED",
      "description": "Volunteer expressed interest."
    },
    {
      "id": 2,
      "name": "CONTACTED",
      "description": "Volunteer has been contacted."
    }
  ]
  ```

### 2. Atualizar o Status de um Voluntário
Para mudar o status de um voluntário. Isso atualizará o `status` atual e adicionará uma entrada no `status_history`.

- **Método:** `PATCH`
- **Endpoint:** `/volunteers/{volunteer_id}/status/`
- **Parâmetros (Query Param):**
    - `new_status_id`: O ID do novo status.
- **Exemplo de Requisição:**
  `PATCH /volunteers/123/status/?new_status_id=2`
- **Autenticação:** Requer token de usuário (Bearer Token).

### 3. Filtrar Voluntários por Status
A listagem de voluntários agora aceita um filtro por `status_id`.

- **Método:** `GET`
- **Endpoint:** `/volunteers/`
- **Parâmetros (Query Param):**
    - `status_id`: (Opcional) ID do status para filtrar.
- **Exemplo de Requisição:**
  `GET /volunteers/?status_id=1` (Retorna apenas voluntários "INTERESTED")

### 4. Detalhes do Voluntário (com Histórico)
Um novo endpoint específico para buscar um voluntário pelo ID foi adicionado, garantindo o retorno completo do histórico.

- **Método:** `GET`
- **Endpoint:** `/volunteers/{volunteer_id}`
- **Exemplo de Resposta:** Retorna o objeto `Volunteer` completo mostrado na seção de Modelos de Dados.

---

## Fluxo de Uso Sugerido (Frontend)

1.  **Tela de Listagem (Kanban ou Tabela):**
    *   Faça uma chamada para `GET /volunteer-statuses/` para obter as colunas do Kanban ou opções de filtro.
    *   Faça chamadas para `GET /volunteers/?status_id=...` para carregar os voluntários de cada coluna/status.

2.  **Movendo um Card (Mudança de Status):**
    *   Quando o usuário arrastar um card de "INTERESTED" para "CONTACTED":
    *   Chame `PATCH /volunteers/{id}/status/?new_status_id={id_contacted}`.
    *   Atualize a interface com a resposta atualizada.

3.  **Tela de Detalhes:**
    *   Ao clicar no voluntário, use `GET /volunteers/{id}`.
    *   Exiba o status atual em destaque.
    *   Exiba uma "Timeline" usando o array `status_history` para mostrar quando cada mudança ocorreu.
