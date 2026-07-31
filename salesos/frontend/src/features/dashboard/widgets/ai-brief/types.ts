export interface AIBriefViewProps {
  summary: string;
  highlights: string[];
  generatedAt: string;
  onRefresh?: () => void;
}
