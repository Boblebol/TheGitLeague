'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import Navigation from '@/components/Navigation';

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [user, setUser] = useState<any>(null);
  const [project, setProject] = useState<any>(null);
  const [repositories, setRepositories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddRepoModal, setShowAddRepoModal] = useState(false);
  const [newRepo, setNewRepo] = useState({
    name: '',
    url: '',
    sync_method: 'push_client',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [copiedText, setCopiedText] = useState('');

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth');
      return;
    }

    try {
      // Fetch user
      const userRes = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (userRes.ok) {
        const userData = await userRes.json();
        setUser(userData);
      } else {
        router.push('/auth');
        return;
      }

      // Fetch project
      const projectRes = await fetch(`http://localhost:8000/api/v1/projects/${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (projectRes.ok) {
        const projectData = await projectRes.json();
        setProject(projectData);
        setRepositories(projectData.repositories || []);
      } else {
        setError('Project not found');
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddRepository = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/repos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newRepo.name,
          url: newRepo.url,
          sync_method: newRepo.sync_method,
          status: 'active',
        }),
      });

      if (response.ok) {
        setSuccess('Repository added successfully!');
        setShowAddRepoModal(false);
        setNewRepo({ name: '', url: '', sync_method: 'push_client' });
        fetchData();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        if (Array.isArray(data.detail)) {
          const errors = data.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
          setError(errors);
        } else if (typeof data.detail === 'string') {
          setError(data.detail);
        } else {
          setError('Failed to add repository');
        }
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleDeleteRepository = async (repoId: string) => {
    if (!confirm('Are you sure you want to remove this repository from the project?')) {
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/repos/${repoId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        setSuccess('Repository removed successfully!');
        fetchData();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to remove repository');
        setTimeout(() => setError(''), 3000);
      }
    } catch (err) {
      setError('Network error. Please try again.');
      setTimeout(() => setError(''), 3000);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(''), 2000);
  };

  const generateYamlConfig = () => {
    if (!project) return '';

    const repoConfigs = repositories.map(repo => `      - path: "/path/to/local/repo"
        git_url: "${repo.url}"`).join('\n');

    return `# GitLeague Client Configuration
api_url: "http://localhost:8000/api/v1"
batch_size: 100
max_retries: 3

projects:
  - name: "${project.name}"
    project_id: "${project.id}"
    repos:
${repoConfigs || '      # Add your repositories here'}
`;
  };

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </main>
    );
  }

  if (!user || !project) {
    return (
      <main className="min-h-screen bg-gray-50">
        <Navigation user={user} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">❌</div>
            <h3 className="text-xl font-semibold mb-2">Project not found</h3>
            <Link
              href="/dashboard/projects"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              ← Back to Projects
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <Navigation user={user} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/dashboard/projects"
            className="text-blue-600 hover:text-blue-700 font-medium mb-4 inline-block"
          >
            ← Back to Projects
          </Link>
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-3xl font-bold">{project.name}</h2>
              {project.description && (
                <p className="text-gray-600 mt-2">{project.description}</p>
              )}
              <div className="flex items-center gap-4 mt-4">
                <div className="flex items-center gap-2">
                  <code className="text-sm bg-gray-100 px-3 py-1 rounded font-mono text-gray-600">
                    ID: {project.id}
                  </code>
                  <button
                    onClick={() => copyToClipboard(project.id, 'id')}
                    className="text-sm text-blue-600 hover:text-blue-700"
                    title="Copy ID"
                  >
                    {copiedText === 'id' ? '✓ Copied' : '📋 Copy'}
                  </button>
                </div>
                {project.slug && (
                  <div className="text-sm text-gray-500">
                    Slug: <code className="bg-gray-100 px-2 py-1 rounded">{project.slug}</code>
                  </div>
                )}
                <span className={`px-3 py-1 text-sm font-medium rounded ${
                  project.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {project.status || 'active'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">{success}</p>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Repositories */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-xl font-bold">Repositories</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {repositories.length} {repositories.length === 1 ? 'repository' : 'repositories'} in this project
                  </p>
                </div>
                <button
                  onClick={() => setShowAddRepoModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                >
                  + Add Repository
                </button>
              </div>

              {repositories.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📦</div>
                  <h4 className="text-lg font-semibold mb-2">No repositories yet</h4>
                  <p className="text-gray-600 mb-6">Add a repository to start tracking commits</p>
                  <button
                    onClick={() => setShowAddRepoModal(true)}
                    className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Add Your First Repository
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {repositories.map((repo: any) => (
                    <div key={repo.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="text-lg font-semibold">{repo.name}</h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded ${
                              repo.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {repo.status || 'active'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 font-mono break-all mb-2">{repo.url}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>Sync: <code className="bg-gray-100 px-1 rounded">{repo.sync_method || 'push_client'}</code></span>
                            <span>Added {new Date(repo.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteRepository(repo.id)}
                          className="ml-4 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Configuration */}
          <div className="lg:col-span-1 space-y-6">
            {/* Python Client Config */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 sticky top-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span>⚙️</span>
                Client Configuration
              </h3>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-semibold text-sm text-gray-700">repos.yaml</h4>
                    <button
                      onClick={() => copyToClipboard(generateYamlConfig(), 'yaml')}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                    >
                      {copiedText === 'yaml' ? '✓ Copied' : '📋 Copy'}
                    </button>
                  </div>
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-md text-xs font-mono overflow-x-auto max-h-96 overflow-y-auto">
                    {generateYamlConfig()}
                  </pre>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-3 text-sm text-gray-700">Quick Start</h4>
                  <ol className="space-y-3 text-sm text-gray-600">
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">1.</span>
                      <span>Install the client: <code className="bg-gray-900 text-gray-100 px-2 py-1 rounded text-xs">pip install thegitleague-client</code></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">2.</span>
                      <span>Copy the YAML config above to <code className="bg-gray-100 px-1 rounded">repos.yaml</code></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">3.</span>
                      <span>Update the <code className="bg-gray-100 px-1 rounded">path</code> fields with your local repository paths</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">4.</span>
                      <span>Get an API key from <Link href="/dashboard/api-keys" className="text-blue-600 hover:text-blue-700">API Keys page</Link></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">5.</span>
                      <span>Set environment variable: <code className="bg-gray-900 text-gray-100 px-2 py-1 rounded text-xs">export GITLEAGUE_API_KEY=your-key</code></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">6.</span>
                      <span>Run sync: <code className="bg-gray-900 text-gray-100 px-2 py-1 rounded text-xs">gitleague-client sync --config repos.yaml</code></span>
                    </li>
                  </ol>
                </div>

                <div className="border-t pt-4">
                  <a
                    href="https://github.com/Boblebol/thegitleague-client"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-center px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    📖 View Documentation
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add Repository Modal */}
      {showAddRepoModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold">Add Repository</h3>
              <button
                onClick={() => {
                  setShowAddRepoModal(false);
                  setError('');
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleAddRepository} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Repository Name *
                </label>
                <input
                  type="text"
                  value={newRepo.name}
                  onChange={(e) => setNewRepo({ ...newRepo, name: e.target.value })}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="my-awesome-repo"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Git URL *
                </label>
                <input
                  type="text"
                  value={newRepo.url}
                  onChange={(e) => setNewRepo({ ...newRepo, url: e.target.value })}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="https://github.com/user/repo.git"
                />
                <p className="text-xs text-gray-500 mt-1">
                  The Git URL of your repository (HTTPS or SSH)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sync Method
                </label>
                <select
                  value={newRepo.sync_method}
                  onChange={(e) => setNewRepo({ ...newRepo, sync_method: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="push_client">Push Client (Recommended)</option>
                  <option value="pull_server">Pull Server</option>
                  <option value="webhook">Webhook</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Use Push Client with the Python client for best results
                </p>
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddRepoModal(false);
                    setError('');
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Add Repository
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
