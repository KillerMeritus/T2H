import { UploadZone } from '../components/Upload/UploadZone';
import { CustomizationPanel } from '../components/Customization/CustomizationPanel';
import { DocumentPreview } from '../components/Preview/DocumentPreview';
import { ProgressBar } from '../components/Progress/ProgressBar';
import { useStore } from '../store';
import { startProcessing, getJobStatus } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Loader2, RefreshCw, LayoutTemplate } from 'lucide-react';

export const Layout = () => {
    const {
        uploadStatus, jobId, config,
        processingStatus, progress, currentStage,
        setProcessingStatus, setProgress, setError, reset, setNumPages
    } = useStore();

    const handleProcess = async () => {
        if (!jobId) return;
        setProcessingStatus('processing');
        try {
            await startProcessing(jobId, config);
            const interval = setInterval(async () => {
                try {
                    const status = await getJobStatus(jobId);
                    setProgress(status.progress, status.current_stage);
                    if (status.status === 'completed') {
                        clearInterval(interval);
                        setProcessingStatus('completed');
                        setNumPages(status.num_pages || 1);
                    } else if (status.status === 'failed') {
                        clearInterval(interval);
                        setProcessingStatus('failed');
                        setError(status.error_message || 'Processing failed');
                    }
                } catch (e) {
                    console.error('Polling error', e);
                }
            }, 1000);
        } catch (error) {
            console.error('Processing failed:', error);
            setProcessingStatus('failed');
            setError('Failed to start processing');
        }
    };

    const handleReset = () => {
        if (confirm('Start over? This will clear current progress.')) reset();
    };

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">

            {/* ─── Header ─── */}
            <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-border">
                <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-serif font-bold text-xl shadow-sm">H</div>
                        <span className="font-serif text-xl font-medium tracking-tight text-foreground">Handwriter</span>
                    </div>
                    <nav>
                        {uploadStatus === 'success' && (
                            <button onClick={handleReset} className="text-sm font-medium text-muted-foreground hover:text-destructive transition-colors flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-secondary">
                                <RefreshCw className="w-3.5 h-3.5" /> Start Over
                            </button>
                        )}
                    </nav>
                </div>
            </header>

            {/* ─── Main ─── */}
            <main className="flex-1 pt-16 flex overflow-hidden">
                <AnimatePresence mode="wait">

                    {/* ── Upload View ── */}
                    {(uploadStatus === 'idle' || uploadStatus === 'uploading' || uploadStatus === 'error') ? (
                        <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.4 }}
                            className="w-full h-full overflow-y-auto flex flex-col items-center justify-center p-6">

                            <div className="text-center mb-12 mt-10">
                                <motion.h1 initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
                                    className="text-5xl md:text-7xl font-serif font-medium tracking-tight mb-6 text-foreground leading-[1.1]">
                                    Turn typed assignments<br />
                                    into <span className="text-primary italic">handwritten notes</span>.
                                </motion.h1>
                                <motion.p initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
                                    className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed font-light">
                                    Convert PDFs into realistic handwriting with authentic imperfections and hand-drawn diagrams.
                                </motion.p>
                            </div>

                            <div className="w-full flex justify-center pb-20">
                                <UploadZone />
                            </div>
                        </motion.div>

                    ) : (
                        /* ── Workspace View ── */
                        <motion.div key="workspace" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
                            className="w-full h-full flex items-stretch">

                            {/* Left: Settings */}
                            <div className="shrink-0 w-80 h-full border-r border-border bg-white z-10 flex flex-col">
                                <CustomizationPanel />
                            </div>

                            {/* Right: Preview */}
                            <div className="flex-1 h-full bg-gray-50 relative flex flex-col min-w-0">

                                {/* Action Bar */}
                                <div className="h-16 border-b border-border bg-white/50 backdrop-blur-sm px-6 flex items-center justify-between shrink-0">
                                    <div className="font-medium text-sm text-muted-foreground flex items-center gap-2">
                                        <LayoutTemplate className="w-4 h-4" />
                                        {processingStatus === 'completed' ? 'Preview Result' : 'Configure & Generate'}
                                    </div>
                                    <div className="flex items-center gap-4">
                                        {(processingStatus === 'idle' || processingStatus === 'completed' || processingStatus === 'failed') ? (
                                            <button onClick={handleProcess}
                                                className="bg-primary text-white px-6 py-2.5 rounded-full font-medium hover:bg-blue-600 transition-all flex items-center gap-2 shadow-lg shadow-blue-200 active:scale-95">
                                                {processingStatus === 'completed' ? 'Regenerate' : 'Convert to Handwriting'}
                                                <ArrowRight className="w-4 h-4" />
                                            </button>
                                        ) : (
                                            <div className="flex items-center gap-3 px-4 py-2 bg-secondary rounded-full border border-border">
                                                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                                                <span className="text-sm font-medium text-foreground">Processing...</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Preview Content */}
                                <div className="flex-1 overflow-hidden relative">
                                    {processingStatus === 'processing' && (
                                        <div className="absolute inset-0 flex items-center justify-center p-12 bg-white/60 backdrop-blur-sm z-20">
                                            <motion.div initial={{ opacity: 0, scale: 0.9, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }}
                                                className="bg-white border border-border p-8 rounded-2xl shadow-2xl max-w-md w-full text-center">
                                                <div className="w-16 h-16 bg-blue-50 text-primary rounded-full flex items-center justify-center mx-auto mb-6 relative">
                                                    <Loader2 className="w-8 h-8 animate-spin" />
                                                </div>
                                                <h3 className="text-xl font-serif font-medium mb-2 text-foreground">Creating your notes</h3>
                                                <p className="text-muted-foreground mb-6 text-sm">
                                                    Applying {config.handwriting_style} style...
                                                </p>
                                                <ProgressBar progress={progress} stage={currentStage} />
                                            </motion.div>
                                        </div>
                                    )}

                                    <div className="h-full p-6 flex flex-col">
                                        {processingStatus === 'completed' ? (
                                            <DocumentPreview />
                                        ) : (
                                            <div className="flex-1 flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-200 rounded-xl m-4 bg-white/50">
                                                <div className="w-24 h-32 border-2 border-dashed border-gray-300 rounded-lg mb-4 opacity-50" />
                                                <p className="font-medium text-foreground/50">Preview will appear here</p>
                                                <p className="text-sm opacity-70">Adjust settings on the left, then click Convert.</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>
        </div>
    );
};
