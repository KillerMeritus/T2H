import { useState } from 'react';
import { useStore } from '../../store';
import { getPreviewUrl, getDownloadUrl } from '../../services/api';
import { ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Download } from 'lucide-react';

export const DocumentPreview = () => {
    const { jobId, numPages } = useStore();
    const [currentPage, setCurrentPage] = useState(1);
    const [zoom, setZoom] = useState(1);

    if (!jobId) return null;

    const totalPages = numPages || 1;

    return (
        <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-border">
                <div className="flex items-center gap-2">
                    <button onClick={() => setZoom(z => Math.max(0.5, z - 0.1))} className="p-1.5 hover:bg-secondary rounded-md transition-colors" title="Zoom Out">
                        <ZoomOut className="w-4 h-4 text-foreground" />
                    </button>
                    <span className="text-sm text-muted-foreground w-14 text-center">{Math.round(zoom * 100)}%</span>
                    <button onClick={() => setZoom(z => Math.min(2, z + 0.1))} className="p-1.5 hover:bg-secondary rounded-md transition-colors" title="Zoom In">
                        <ZoomIn className="w-4 h-4 text-foreground" />
                    </button>
                </div>

                <div className="flex items-center gap-2">
                    <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage <= 1} className="p-1.5 hover:bg-secondary rounded-md disabled:opacity-30 transition-colors">
                        <ChevronLeft className="w-4 h-4 text-foreground" />
                    </button>
                    <span className="text-sm text-foreground">{currentPage} / {totalPages}</span>
                    <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage >= totalPages} className="p-1.5 hover:bg-secondary rounded-md disabled:opacity-30 transition-colors">
                        <ChevronRight className="w-4 h-4 text-foreground" />
                    </button>
                </div>

                <a
                    href={getDownloadUrl(jobId)}
                    download
                    className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
                >
                    <Download className="w-4 h-4" /> Download PDF
                </a>
            </div>

            {/* Preview Canvas */}
            <div className="flex-1 overflow-auto bg-gray-100 flex items-center justify-center p-8">
                <div
                    style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
                    className="transition-transform duration-200 shadow-2xl rounded-sm"
                >
                    <img
                        src={getPreviewUrl(jobId, currentPage)}
                        alt={`Page ${currentPage}`}
                        className="max-w-full bg-white"
                        style={{ minWidth: '595px', minHeight: '842px' }}
                    />
                </div>
            </div>
        </div>
    );
};
