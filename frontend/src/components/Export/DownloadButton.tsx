import { getDownloadUrl } from '../../services/api';
import { useStore } from '../../store';
import { Download } from 'lucide-react';

export const DownloadButton = () => {
    const { jobId } = useStore();

    if (!jobId) return null;

    return (
        <a
            href={getDownloadUrl(jobId)}
            download
            className="flex items-center gap-2 bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors shadow-md"
        >
            <Download className="w-5 h-5" /> Download PDF
        </a>
    );
};
