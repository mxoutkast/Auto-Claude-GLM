import { ChevronDown, ChevronUp, Terminal } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';

interface MergeProgressEvent {
    taskId: string;
    type: 'stdout' | 'stderr';
    message: string;
    timestamp: number;
}

interface MergeProgressPanelProps {
    taskId: string;
    isActive: boolean;
    onToggle?: () => void;
}

/**
 * Displays real-time merge progress output from Python subprocess
 * Shows stdout/stderr streams as they arrive
 */
export function MergeProgressPanel({ taskId, isActive, onToggle }: MergeProgressPanelProps) {
    const [isExpanded, setIsExpanded] = useState(true);
    const [logs, setLogs] = useState<MergeProgressEvent[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);
    const [autoScroll, setAutoScroll] = useState(true);

    // Listen for merge progress events
    useEffect(() => {
        if (!isActive) {
            return;
        }

        const handleProgress = (_event: unknown, data: MergeProgressEvent) => {
            if (data.taskId === taskId) {
                setLogs(prev => [...prev, data]);
            }
        };

        window.electronAPI.onMergeProgress?.(handleProgress);

        return () => {
            // Cleanup listener when component unmounts or merge completes
            window.electronAPI.offMergeProgress?.(handleProgress);
        };
    }, [taskId, isActive]);

    // Auto-scroll to bottom when new logs arrive
    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, autoScroll]);

    // Clear logs when merge starts
    useEffect(() => {
        if (isActive) {
            setLogs([]);
            setIsExpanded(true);
        }
    }, [isActive]);

    // Handle manual scroll - disable auto-scroll if user scrolls up
    const handleScroll = () => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            const isAtBottom = scrollHeight - scrollTop - clientHeight < 10;
            setAutoScroll(isAtBottom);
        }
    };

    if (!isActive && logs.length === 0) {
        return null;
    }

    return (
        <div className="rounded-xl border border-border bg-secondary/30 overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between p-3 hover:bg-secondary/50 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-foreground">
                        {isActive ? 'AI Merge Progress (Live)' : 'AI Merge Progress'}
                    </span>
                    {isActive && (
                        <span className="inline-flex h-2 w-2 rounded-full bg-success animate-pulse" />
                    )}
                </div>
                {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
            </button>

            {/* Log output */}
            {isExpanded && (
                <div className="border-t border-border">
                    <div
                        ref={scrollRef}
                        onScroll={handleScroll}
                        className="max-h-64 overflow-y-auto bg-background/50 p-3 font-mono text-xs"
                    >
                        {logs.length === 0 ? (
                            <div className="text-muted-foreground italic">
                                Waiting for merge output...
                            </div>
                        ) : (
                            logs.map((log, index) => (
                                <div
                                    key={index}
                                    className={cn(
                                        'whitespace-pre-wrap break-words',
                                        log.type === 'stderr' && !log.message.includes('[AI-MERGE]')
                                            ? 'text-muted-foreground'
                                            : 'text-foreground'
                                    )}
                                >
                                    {log.message}
                                </div>
                            ))
                        )}
                    </div>
                    {!autoScroll && (
                        <div className="p-2 bg-warning/10 border-t border-warning/30">
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                    setAutoScroll(true);
                                    if (scrollRef.current) {
                                        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
                                    }
                                }}
                                className="w-full text-xs"
                            >
                                ↓ Scroll to bottom
                            </Button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
