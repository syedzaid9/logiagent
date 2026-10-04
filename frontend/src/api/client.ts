const metaEnv = (import.meta as any).env || {};
const BASE_URL = (metaEnv.VITE_API_BASE_URL ? `${metaEnv.VITE_API_BASE_URL.replace(/\/$/, '')}/api/v1` : '/api/v1');

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
      `Cannot connect to backend server at ${BASE_URL}. Please verify the LogiAgent backend service is running and accessible.`
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
