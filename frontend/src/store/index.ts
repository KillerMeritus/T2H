import { create } from 'zustand';

interface ProcessConfig {
    handwriting_style: string;
    imperfection_level: number;
    paper_type: string;
    ink_color: string;
    line_spacing: number;
    font_size: number;
}

interface AppState {
    file: File | null;
    jobId: string | null;
    uploadStatus: 'idle' | 'uploading' | 'success' | 'error';
    processingStatus: 'idle' | 'processing' | 'completed' | 'failed';
    progress: number;
    currentStage: string;
    error: string | null;
    numPages: number;
    config: ProcessConfig;

    setFile: (file: File) => void;
    setJobId: (id: string) => void;
    setUploadStatus: (status: AppState['uploadStatus']) => void;
    setProcessingStatus: (status: AppState['processingStatus']) => void;
    setProgress: (progress: number, stage: string) => void;
    setError: (error: string | null) => void;
    setConfig: (config: Partial<ProcessConfig>) => void;
    setNumPages: (n: number) => void;
    reset: () => void;
}

const defaultConfig: ProcessConfig = {
    handwriting_style: 'Caveat',
    imperfection_level: 0.05,
    paper_type: 'lined',
    ink_color: '#1a1a2e',
    line_spacing: 1.5,
    font_size: 16,
};

export const useStore = create<AppState>((set) => ({
    file: null,
    jobId: null,
    uploadStatus: 'idle',
    processingStatus: 'idle',
    progress: 0,
    currentStage: '',
    error: null,
    numPages: 0,
    config: { ...defaultConfig },

    setFile: (file) => set({ file }),
    setJobId: (jobId) => set({ jobId }),
    setUploadStatus: (uploadStatus) => set({ uploadStatus }),
    setProcessingStatus: (processingStatus) => set({ processingStatus }),
    setProgress: (progress, currentStage) => set({ progress, currentStage }),
    setError: (error) => set({ error }),
    setConfig: (partial) => set((s) => ({ config: { ...s.config, ...partial } })),
    setNumPages: (numPages) => set({ numPages }),
    reset: () => set({
        file: null,
        jobId: null,
        uploadStatus: 'idle',
        processingStatus: 'idle',
        progress: 0,
        currentStage: '',
        error: null,
        numPages: 0,
        config: { ...defaultConfig },
    }),
}));
