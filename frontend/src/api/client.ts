const BASE_URL = '/api/v1';

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('logiagent_token');
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  } catch (netErr: any) {
    throw new Error(
      `Cannot connect to backend server. Please verify the FastAPI backend is running on http://localhost:8000.`
    );
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = 
      (typeof errorData.error === 'object' && errorData.error?.message) ||
      (typeof errorData.detail === 'string' ? errorData.detail : null) ||
      (Array.isArray(errorData.detail) && errorData.detail[0]?.message ? errorData.detail[0].message : null) ||
      errorData.message ||
      `Request failed with status ${response.status}`;
      
    throw new Error(message);
  }

  return response.json();
}
