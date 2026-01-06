'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navigation from '@/components/Navigation';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        router.push('/auth');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data);

          // Fetch basic stats
          try {
            const statsRes = await fetch('http://localhost:8000/api/v1/projects', {
              headers: { 'Authorization': `Bearer ${token}` },
            });
            if (statsRes.ok) {
              const projects = await statsRes.json();
              setStats({ projectCount: projects.length });
            }
          } catch (err) {
            console.error('Failed to fetch stats:', err);
          }
        } else {
          localStorage.removeItem('access_token');
          router.push('/auth');
        }
      } catch (err) {
        console.error('Failed to fetch user:', err);
        router.push('/auth');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCurrentUser();
  }, [router]);

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  const isCommissioner = user.role === 'commissioner';

  return (
    <main className="min-h-screen bg-gray-50">
      <Navigation user={user} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">
            Welcome{user.display_name ? `, ${user.display_name}` : ''}!
          </h2>
          <p className="text-gray-600">{user.email}</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Role</h3>
              {isCommissioner && <span className="text-2xl">👑</span>}
            </div>
            <p className="text-2xl font-bold text-blue-600 uppercase">
              {user.role}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Status</h3>
            <p className="text-2xl font-bold text-green-600 uppercase">
              {user.status}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Projects</h3>
            <p className="text-2xl font-bold text-purple-600">
              {stats?.projectCount || 0}
            </p>
          </div>
        </div>

        {/* Commissioner Panel */}
        {isCommissioner && (
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200 rounded-lg p-6 mb-8">
            <div className="flex items-start gap-3 mb-6">
              <span className="text-3xl">👑</span>
              <div>
                <h3 className="text-xl font-bold text-yellow-900 mb-2">
                  Commissioner Dashboard
                </h3>
                <p className="text-yellow-800">
                  You have full administrative control over The Git League
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link
                href="/dashboard/projects"
                className="bg-white rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="text-2xl mb-2">📁</div>
                <h4 className="font-semibold mb-1">Manage Projects</h4>
                <p className="text-sm text-gray-600">Create and configure Git repositories</p>
              </Link>
              <Link
                href="/dashboard/players"
                className="bg-white rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="text-2xl mb-2">👥</div>
                <h4 className="font-semibold mb-1">Approve Players</h4>
                <p className="text-sm text-gray-600">Review and manage league members</p>
              </Link>
              <Link
                href="/dashboard/api-keys"
                className="bg-white rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="text-2xl mb-2">🔑</div>
                <h4 className="font-semibold mb-1">API Access</h4>
                <p className="text-sm text-gray-600">Generate keys for automation</p>
              </Link>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <span>📁</span>
              Projects
            </h3>
            <p className="text-gray-600 mb-4">
              {stats?.projectCount > 0
                ? `You have ${stats.projectCount} ${stats.projectCount === 1 ? 'project' : 'projects'}`
                : 'No projects yet. Create your first project to start tracking contributions.'}
            </p>
            <Link
              href="/dashboard/projects"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              {stats?.projectCount > 0 ? 'View Projects' : 'Create Project'}
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <span>🔑</span>
              API Integration
            </h3>
            <p className="text-gray-600 mb-4">
              Generate API keys to use the Python client for automated Git tracking and CI/CD integration.
            </p>
            <Link
              href="/dashboard/api-keys"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Manage API Keys
            </Link>
          </div>
        </div>

        {/* Git Identities */}
        {user.git_identities && user.git_identities.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h3 className="text-xl font-semibold mb-4">Your Git Identities</h3>
            <div className="space-y-3">
              {user.git_identities.map((identity: any) => (
                <div key={identity.id} className="border rounded-md p-4 flex items-center gap-3">
                  <span className="text-2xl">📧</span>
                  <div>
                    {identity.git_name && (
                      <p className="font-medium">{identity.git_name}</p>
                    )}
                    <p className="text-sm text-gray-600">{identity.git_email}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Getting Started Guide */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-6">🚀 Getting Started</h3>
          <div className="space-y-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center font-bold text-blue-600">
                1
              </div>
              <div>
                <h4 className="font-semibold mb-1">Create a Project</h4>
                <p className="text-sm text-gray-600 mb-2">
                  Set up your first project and link your Git repository to start tracking contributions.
                </p>
                <Link href="/dashboard/projects" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                  Go to Projects →
                </Link>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center font-bold text-blue-600">
                2
              </div>
              <div>
                <h4 className="font-semibold mb-1">Generate an API Key</h4>
                <p className="text-sm text-gray-600 mb-2">
                  Create an API key to use the Python client for automated syncing and CI/CD integration.
                </p>
                <Link href="/dashboard/api-keys" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                  Manage API Keys →
                </Link>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center font-bold text-blue-600">
                3
              </div>
              <div>
                <h4 className="font-semibold mb-1">Install the Python Client</h4>
                <p className="text-sm text-gray-600 mb-2">
                  Use our Python client to sync your repositories and track contributions automatically.
                </p>
                <div className="bg-gray-900 text-gray-100 p-3 rounded-md text-sm font-mono mt-2">
                  pip install thegitleague-client
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center font-bold text-blue-600">
                4
              </div>
              <div>
                <h4 className="font-semibold mb-1">Watch Your Stats Grow</h4>
                <p className="text-sm text-gray-600">
                  Once configured, your Git commits will be tracked and you&apos;ll see NBA-style statistics for your development work!
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
