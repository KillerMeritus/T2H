import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});

export interface ProcessConfig {
    handwriting_style: string;
    imperfection_level: number;
    paper_type: string;
    ink_color: string;
    line_spacing: number;
    font_size: number;
}

export interface JobStatus {
    job_id: string;
    status: 'uploaded' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string;
    num_pages: number;
    error_message?: string;
}

export const uploadPDF = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<{ job_id: string; status: string; filename: string; pages: number }>(
        '/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
};

export const startProcessing = async (jobId: string, config: ProcessConfig) => {
    const response = await api.post(`/process/${jobId}`, { config });
    return response.data;
};

export const getJobStatus = async (jobId: string) => {
    const response = await api.get<JobStatus>(`/status/${jobId}`);
    return response.data;

};

export const getDownloadUrl = (jobId: string, format: 'pdf' | 'png' | 'jpg' = 'pdf') =>
    `${API_URL}/download/${jobId}?format=${format}`;

export const getPreviewUrl = (jobId: string, pageNum: number) =>
    `${API_URL}/preview/${jobId}/${pageNum}`;
