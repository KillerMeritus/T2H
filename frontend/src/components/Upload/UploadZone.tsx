import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { uploadPDF } from '../../services/api';
import { useStore } from '../../store';
import { motion, AnimatePresence } from 'framer-motion';

export const UploadZone = () => {
    const [isDragReject, setIsDragReject] = useState(false);
    const { setFile, setJobId, setUploadStatus, uploadStatus, setError } = useStore();

    const onDrop = useCallback(async (acceptedFiles: File[], fileRejections: unknown[]) => {
        if (fileRejections.length > 0) {
            setIsDragReject(true);
            setTimeout(() => setIsDragReject(false), 2000);
            return;
        }
        const file = acceptedFiles[0];
        if (!file) return;

        setFile(file);
        setUploadStatus('uploading');
        setError(null);

        try {
            const response = await uploadPDF(file);
            setJobId(response.job_id);
            setUploadStatus('success');
        } catch (err) {
            console.error('Upload failed:', err);
            setUploadStatus('error');
            setError('Failed to upload file. Please try again.');
        }
    }, [setFile, setJobId, setUploadStatus, setError]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        maxSize: 50 * 1024 * 1024,
        multiple: false,
    });

    return (
        <div className="w-full max-w-2xl mx-auto mt-8">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
                <div
                    {...getRootProps()}
                    className={`
            relative group cursor-pointer border-2 border-dashed rounded-xl p-16
            flex flex-col items-center justify-center text-center transition-all duration-300
            ${isDragActive ? 'border-primary bg-blue-50 scale-[1.02]' : 'border-border hover:border-primary/50 hover:bg-muted/30'}
            ${isDragReject ? 'border-destructive bg-red-50' : ''}
          `}
                >
                    <input {...getInputProps()} />

                    <AnimatePresence mode="wait">
                        {uploadStatus === 'uploading' ? (
                            <motion.div key="uploading" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }} className="flex flex-col items-center">
                                <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                                <h3 className="text-xl font-medium font-serif text-foreground">Uploading...</h3>
                                <p className="text-muted-foreground mt-2">Just a moment</p>
                            </motion.div>
                        ) : uploadStatus === 'success' ? (
                            <motion.div key="success" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }} className="flex flex-col items-center">
                                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                                    <FileText className="w-8 h-8 text-green-600" />
                                </div>
                                <h3 className="text-xl font-medium font-serif text-foreground">File Uploaded</h3>
                                <p className="text-muted-foreground mt-2">Ready to process</p>
                            </motion.div>
                        ) : (
                            <motion.div key="idle" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }} className="flex flex-col items-center">
                                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-colors duration-300 ${isDragActive ? 'bg-primary text-white' : 'bg-secondary text-secondary-foreground group-hover:bg-blue-50 group-hover:text-primary'}`}>
                                    <Upload className="w-8 h-8" />
                                </div>
                                <h3 className="text-2xl font-serif font-medium text-foreground mb-3">Upload Assignment PDF</h3>
                                <p className="text-muted-foreground max-w-sm leading-relaxed">
                                    Drag & drop your file here, or click to select.<br />
                                    <span className="text-sm opacity-70">Supports PDF up to 50MB</span>
                                </p>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {isDragReject && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="absolute bottom-4 left-0 right-0 flex justify-center">
                            <div className="bg-red-50 text-destructive px-4 py-2 rounded-full flex items-center text-sm font-medium">
                                <AlertCircle className="w-4 h-4 mr-2" /> Only PDF files are allowed
                            </div>
                        </motion.div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};
