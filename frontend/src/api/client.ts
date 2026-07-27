const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const method = options?.method || 'GET';
  console.log(`[API REQUEST] ${method} ${url}`);

  const isDelete = method.toUpperCase() === 'DELETE';
  const headers: Record<string, string> = {};
  
  // Do NOT set Content-Type: application/json for DELETE requests without body
  if (!isDelete && options?.body) {
    headers['Content-Type'] = 'application/json';
  }
  if (options?.headers) {
    Object.assign(headers, options.headers);
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`[API ERROR ${response.status}] ${url}: ${errorBody}`);
      throw new Error(`API call failed [${response.status}]: ${errorBody || response.statusText}`);
    }

    if (response.status === 204) {
      return null as T;
    }

    const text = await response.text();
    if (!text || !text.trim()) {
      return null as T;
    }

    return JSON.parse(text);
  } catch (err: any) {
    console.error(`[FETCH FAILED] ${method} ${url}:`, err);
    throw err;
  }
}

export const api = {
  // Dashboard
  getDashboardStats: () => fetchApi<any>('/dashboard/stats'),

  // Candidates
  getCandidates: (params?: { search?: string; skill?: string; location?: string; min_exp?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append('search', params.search);
    if (params?.skill) searchParams.append('skill', params.skill);
    if (params?.location) searchParams.append('location', params.location);
    if (params?.min_exp) searchParams.append('min_exp', params.min_exp.toString());
    const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return fetchApi<any[]>(`/candidates${queryStr}`);
  },
  getCandidate: (id: string) => fetchApi<any>(`/candidates/${id}`),
  createCandidate: (data: any) => fetchApi<any>('/candidates', { method: 'POST', body: JSON.stringify(data) }),
  updateCandidate: (id: string, data: any) => fetchApi<any>(`/candidates/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  updateCandidateProfile: (id: string, data: any) => fetchApi<any>(`/candidates/${id}/profile`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCandidate: (id: string) => fetchApi<void>(`/candidates/${id}`, { method: 'DELETE' }),

  // Requirements & Matching
  getRequirements: () => fetchApi<any[]>('/requirements'),
  getRequirement: (id: string) => fetchApi<any>(`/requirements/${id}`),
  createRequirement: (data: any) => fetchApi<any>('/requirements', { method: 'POST', body: JSON.stringify(data) }),
  updateRequirement: (id: string, data: any) => fetchApi<any>(`/requirements/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteRequirement: (id: string) => fetchApi<void>(`/requirements/${id}`, { method: 'DELETE' }),

  // Match Analysis
  matchRequirement: (id: string) => fetchApi<any>(`/requirements/${id}/match`, { method: 'POST' }),
  getRequirementMatches: (id: string) => fetchApi<any[]>(`/requirements/${id}/matches`),
  getCandidateMatchDetails: (reqId: string, candId: string) => fetchApi<any>(`/requirements/${reqId}/matches/${candId}`),

  // Resumes
  uploadResumes: async (files: File[]): Promise<any> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const response = await fetch(`${API_BASE_URL}/resumes/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Upload failed [${response.status}]: ${errorBody}`);
    }

    return response.json();
  },
};
