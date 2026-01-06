'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navigation from '@/components/Navigation';

export default function PlayersPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [players, setPlayers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'retired'>('all');
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

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

        // Check if user is commissioner
        if (userData.role !== 'commissioner') {
          router.push('/dashboard');
          return;
        }
      } else {
        router.push('/auth');
        return;
      }

      // Fetch all users (players) - API returns paginated response with "items" array
      const usersRes = await fetch('http://localhost:8000/api/v1/users?limit=100', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        // API returns { items: [...], total, page, pages }
        if (usersData.items && Array.isArray(usersData.items)) {
          setPlayers(usersData.items);
        } else if (Array.isArray(usersData)) {
          // Fallback if API returns array directly
          setPlayers(usersData);
        } else {
          console.error('Users data has invalid format:', usersData);
          setLoadError('Invalid data format received from server');
          setPlayers([]);
        }
      } else {
        const errorData = await usersRes.json();
        setLoadError(errorData.detail || 'Failed to fetch players');
        setPlayers([]);
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setLoadError('Network error. Please try again.');
      setPlayers([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateUserStatus = async (userId: string, newStatus: string) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/users/${userId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        setSuccess(`Player ${newStatus} successfully!`);
        setTimeout(() => setSuccess(''), 3000);
        fetchData();
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update player status');
        setTimeout(() => setError(''), 3000);
      }
    } catch (err) {
      setError('Network error. Please try again.');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleUpdateUserRole = async (userId: string, newRole: string) => {
    if (!confirm(`Are you sure you want to change this user's role to ${newRole.toUpperCase()}?`)) {
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/users/${userId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: newRole }),
      });

      if (response.ok) {
        setSuccess(`Role updated to ${newRole} successfully!`);
        setTimeout(() => setSuccess(''), 3000);
        fetchData();
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update player role');
        setTimeout(() => setError(''), 3000);
      }
    } catch (err) {
      setError('Network error. Please try again.');
      setTimeout(() => setError(''), 3000);
    }
  };

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </main>
    );
  }

  if (!user) return null;

  // Ensure players is always an array before filtering
  const playersArray = Array.isArray(players) ? players : [];

  const filteredPlayers = playersArray.filter(p =>
    filter === 'all' ? true : p.status === filter
  );

  const pendingCount = playersArray.filter(p => p.status === 'pending').length;
  const approvedCount = playersArray.filter(p => p.status === 'approved').length;
  const retiredCount = playersArray.filter(p => p.status === 'retired').length;

  return (
    <main className="min-h-screen bg-gray-50">
      <Navigation user={user} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Players Management</h2>
          <p className="text-gray-600">Approve players, manage roles, and monitor the league</p>
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

        {loadError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{loadError}</p>
            <p className="text-xs text-red-600 mt-2">
              The API endpoint may not exist yet. Check backend logs.
            </p>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <button
            onClick={() => setFilter('all')}
            className={`p-6 rounded-lg transition-all ${
              filter === 'all'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white hover:shadow-md'
            }`}
          >
            <div className="text-3xl font-bold">{playersArray.length}</div>
            <div className="text-sm mt-1 opacity-90">Total Players</div>
          </button>

          <button
            onClick={() => setFilter('pending')}
            className={`p-6 rounded-lg transition-all ${
              filter === 'pending'
                ? 'bg-yellow-600 text-white shadow-lg'
                : 'bg-white hover:shadow-md'
            }`}
          >
            <div className="text-3xl font-bold">{pendingCount}</div>
            <div className="text-sm mt-1 opacity-90">Pending Approval</div>
          </button>

          <button
            onClick={() => setFilter('approved')}
            className={`p-6 rounded-lg transition-all ${
              filter === 'approved'
                ? 'bg-green-600 text-white shadow-lg'
                : 'bg-white hover:shadow-md'
            }`}
          >
            <div className="text-3xl font-bold">{approvedCount}</div>
            <div className="text-sm mt-1 opacity-90">Approved</div>
          </button>

          <button
            onClick={() => setFilter('retired')}
            className={`p-6 rounded-lg transition-all ${
              filter === 'retired'
                ? 'bg-gray-600 text-white shadow-lg'
                : 'bg-white hover:shadow-md'
            }`}
          >
            <div className="text-3xl font-bold">{retiredCount}</div>
            <div className="text-sm mt-1 opacity-90">Retired</div>
          </button>
        </div>

        {/* Players Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Player
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Git Identities
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredPlayers.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      No players found with status: {filter}
                    </td>
                  </tr>
                ) : (
                  filteredPlayers.map((player: any) => (
                    <tr key={player.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {player.display_name || 'Unnamed Player'}
                          </div>
                          <div className="text-sm text-gray-500">{player.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {player.role === 'commissioner' && <span>👑</span>}
                          <select
                            value={player.role}
                            onChange={(e) => handleUpdateUserRole(player.id, e.target.value)}
                            disabled={player.id === user.id}
                            className="text-sm border border-gray-300 rounded px-2 py-1 uppercase disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <option value="spectator">Spectator</option>
                            <option value="player">Player</option>
                            <option value="commissioner">Commissioner</option>
                          </select>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full uppercase ${
                          player.status === 'approved'
                            ? 'bg-green-100 text-green-800'
                            : player.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {player.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {player.git_identities?.length || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(player.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {player.status === 'pending' && (
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleUpdateUserStatus(player.id, 'approved')}
                              className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleUpdateUserStatus(player.id, 'retired')}
                              className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                        {player.status === 'approved' && player.id !== user.id && (
                          <button
                            onClick={() => handleUpdateUserStatus(player.id, 'retired')}
                            className="px-3 py-1 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                          >
                            Retire
                          </button>
                        )}
                        {player.status === 'retired' && (
                          <button
                            onClick={() => handleUpdateUserStatus(player.id, 'approved')}
                            className="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          >
                            Reactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
}
