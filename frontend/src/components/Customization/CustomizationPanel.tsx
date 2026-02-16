import { useStore } from '../../store';
import { Settings2, PenTool, FileType, Minus, Palette } from 'lucide-react';

export const CustomizationPanel = () => {
    const { config, setConfig } = useStore();

    return (
        <div className="bg-card w-full flex flex-col h-full overflow-y-auto">
            <div className="p-6 border-b border-border">
                <h2 className="font-serif text-xl font-medium flex items-center gap-2 text-foreground">
                    <Settings2 className="w-5 h-5" /> Customize
                </h2>
            </div>

            <div className="p-6 space-y-8">
                {/* Handwriting Style */}
                <section>
                    <label className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                        <PenTool className="w-4 h-4" /> Handwriting Style
                    </label>
                    <div className="grid grid-cols-1 gap-2 mt-3">
                        {['Caveat', 'Indie Flower', 'Permanent Marker', 'Patrick Hand'].map((font) => (
                            <button
                                key={font}
                                onClick={() => setConfig({ handwriting_style: font })}
                                className={`px-4 py-3 rounded-lg text-left transition-all border ${config.handwriting_style === font
                                        ? 'bg-blue-50 border-primary text-primary'
                                        : 'bg-secondary/30 border-transparent hover:bg-secondary/60 text-foreground'
                                    }`}
                            >
                                <span className="text-lg" style={{ fontFamily: font }}>{font}</span>
                            </button>
                        ))}
                    </div>
                </section>

                {/* Paper Type */}
                <section>
                    <label className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                        <FileType className="w-4 h-4" /> Paper Type
                    </label>
                    <div className="grid grid-cols-2 gap-2 mt-3">
                        {['lined', 'graph', 'blank', 'engineering'].map((type) => (
                            <button
                                key={type}
                                onClick={() => setConfig({ paper_type: type })}
                                className={`px-3 py-2 rounded-md text-sm capitalize transition-all border ${config.paper_type === type
                                        ? 'bg-blue-50 border-primary text-primary font-medium'
                                        : 'bg-secondary/30 border-transparent hover:bg-secondary/60 text-foreground'
                                    }`}
                            >
                                {type}
                            </button>
                        ))}
                    </div>
                </section>

                {/* Imperfection Level */}
                <section>
                    <label className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                        <Minus className="w-4 h-4" /> Imperfection Level
                    </label>
                    <div className="flex items-center gap-4 mt-3">
                        <input
                            type="range"
                            min="0" max="0.2" step="0.01"
                            value={config.imperfection_level}
                            onChange={(e) => setConfig({ imperfection_level: parseFloat(e.target.value) })}
                            className="flex-1 h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                        />
                        <span className="text-sm w-12 text-right text-foreground">
                            {Math.round(config.imperfection_level * 100)}%
                        </span>
                    </div>
                </section>

                {/* Ink Color */}
                <section>
                    <label className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                        <Palette className="w-4 h-4" /> Ink Color
                    </label>
                    <div className="flex gap-3 mt-3">
                        {['#1a1a2e', '#000000', '#1a3c7a', '#7a1a1a'].map((color) => (
                            <button
                                key={color}
                                onClick={() => setConfig({ ink_color: color })}
                                className={`w-8 h-8 rounded-full border-2 transition-transform hover:scale-110 ${config.ink_color === color ? 'border-primary ring-2 ring-blue-200' : 'border-gray-300'
                                    }`}
                                style={{ backgroundColor: color }}
                            />
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
};
