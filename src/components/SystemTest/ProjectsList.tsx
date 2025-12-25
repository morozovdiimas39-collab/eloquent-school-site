import Icon from '@/components/ui/icon';

interface Project {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'building' | 'deployed';
  createdAt: string;
  files: any[];
  url?: string;
  color: string;
}

interface ProjectsListProps {
  projects: Project[];
  selectedProject: Project | null;
  onSelectProject: (project: Project) => void;
  isLoading: boolean;
}

const getStatusIcon = (status: Project['status']) => {
  switch(status) {
    case 'deployed': return { icon: 'CheckCircle2', color: 'text-emerald-400' };
    case 'building': return { icon: 'Loader2', color: 'text-amber-400 animate-spin' };
    default: return { icon: 'Circle', color: 'text-slate-400' };
  }
};

export default function ProjectsList({ projects, selectedProject, onSelectProject, isLoading }: ProjectsListProps) {
  if (isLoading) {
    return (
      <div className="lg:col-span-3 space-y-4">
        <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-5 shadow-2xl">
          <div className="flex items-center justify-center h-32">
            <Icon name="Loader2" size={32} className="text-purple-400 animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="lg:col-span-3 space-y-4">
      <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-5 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Проекты</h2>
          <div className="px-3 py-1 bg-purple-500/20 rounded-full text-purple-300 text-sm font-medium">
            {projects.length}
          </div>
        </div>

        <div className="space-y-2 max-h-[520px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
          {projects.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <Icon name="FolderOpen" size={32} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">Нет проектов</p>
              <p className="text-xs mt-1">Создайте первый проект</p>
            </div>
          ) : (
            projects.map(project => {
              const statusInfo = getStatusIcon(project.status);
              return (
                <div
                  key={project.id}
                  onClick={() => onSelectProject(project)}
                  className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-300 ${
                    selectedProject?.id === project.id
                      ? 'bg-gradient-to-r from-purple-600/20 to-pink-600/20 border-2 border-purple-500/50 shadow-lg shadow-purple-500/20'
                      : 'bg-white/5 hover:bg-white/10 border-2 border-transparent hover:border-white/20'
                  }`}
                >
                  <div className={`absolute inset-0 bg-gradient-to-r ${project.color} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity`}></div>
                  
                  <div className="relative">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-white font-semibold text-sm flex-1 truncate pr-2">
                        {project.name}
                      </h3>
                      <Icon name={statusInfo.icon as any} size={18} className={statusInfo.color} />
                    </div>
                    
                    <p className="text-slate-400 text-xs mb-3 line-clamp-2 leading-relaxed">
                      {project.description}
                    </p>
                    
                    <div className="flex items-center gap-3 text-xs">
                      <div className="flex items-center gap-1.5 text-slate-400">
                        <Icon name="FileCode" size={14} />
                        <span>{project.files.length}</span>
                      </div>
                      {project.url && (
                        <a 
                          href={project.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Icon name="ExternalLink" size={14} />
                          <span>Open</span>
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-5 shadow-2xl">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Icon name="BarChart3" size={18} />
          Статистика
        </h3>
        <div className="space-y-3">
          {[
            { label: 'Активных', value: projects.filter(p => p.status === 'active').length, color: 'from-blue-500 to-cyan-500' },
            { label: 'Развернутых', value: projects.filter(p => p.status === 'deployed').length, color: 'from-emerald-500 to-teal-500' },
            { label: 'Файлов', value: projects.reduce((acc, p) => acc + p.files.length, 0), color: 'from-purple-500 to-pink-500' },
          ].map((stat, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
              <span className="text-slate-400 text-sm">{stat.label}</span>
              <div className="relative">
                <div className={`absolute inset-0 bg-gradient-to-r ${stat.color} blur-lg opacity-30`}></div>
                <div className={`relative px-3 py-1 bg-gradient-to-r ${stat.color} rounded-lg text-white font-bold text-sm`}>
                  {stat.value}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
