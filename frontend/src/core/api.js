const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export async function apiRequest(endpoint, method = 'GET', body = null) {
    const config = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) config.body = JSON.stringify(body);

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || `Erro ${response.status}`);
    }
    return data;
}