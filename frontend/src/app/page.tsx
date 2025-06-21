'use client';

import { useState, useEffect } from 'react';
import { Plus, RefreshCw, Activity, Globe, Clock, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AddSiteDialog } from '@/components/AddSiteDialog';
import { SitesList } from '@/components/SitesList';
import { StatusPanel } from '@/components/StatusPanel';
import { getSitesStatus, getMonitorStats, triggerManualCheck, type SiteStatus, type MonitorStats } from '@/lib/api';

export default function Home() {
  const [sites, setSites] = useState<SiteStatus[]>([]);
  const [stats, setStats] = useState<MonitorStats | null>(null);
  const [selectedSite, setSelectedSite] = useState<SiteStatus | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isChecking, setIsChecking] = useState(false);

  const fetchData = async () => {
    try {
      const [sitesData, statsData] = await Promise.all([
        getSitesStatus(),
        getMonitorStats()
      ]);
      setSites(sitesData);
      setStats(statsData);
      
      // Auto-select first site if none selected
      if (!selectedSite && sitesData.length > 0) {
        setSelectedSite(sitesData[0]);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleManualCheck = async () => {
    setIsChecking(true);
    try {
      await triggerManualCheck();
      await fetchData(); // Refresh data after check
    } catch (error) {
      console.error('Failed to trigger manual check:', error);
    } finally {
      setIsChecking(false);
    }
  };

  const handleSiteAdded = () => {
    fetchData(); // Refresh data when new site is added
  };

  const handleSiteDeleted = () => {
    fetchData(); // Refresh data when site is deleted
    setSelectedSite(null); // Clear selection
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-6 w-6 text-blue-600" />
            <h1 className="text-2xl font-bold">SiteUp Monitor</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Stats */}
            {stats && (
              <div className="flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-1">
                  <Globe className="h-4 w-4 text-gray-500" />
                  <span>{stats.total_sites} sites</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="h-2 w-2 rounded-full bg-green-500"></div>
                  <span>{stats.sites_up} up</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="h-2 w-2 rounded-full bg-red-500"></div>
                  <span>{stats.sites_down} down</span>
                </div>
                {stats.average_response_time && (
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4 text-gray-500" />
                    <span>{Math.round(stats.average_response_time * 1000)}ms avg</span>
                  </div>
                )}
              </div>
            )}
            
            {/* Actions */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleManualCheck}
              disabled={isChecking}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isChecking ? 'animate-spin' : ''}`} />
              Check Now
            </Button>
            
            <Button size="sm" onClick={() => setIsAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Site
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Sites List */}
        <div className="w-80 border-r bg-gray-50/40 flex flex-col">
          <div className="p-4 border-b bg-white">
            <h2 className="font-semibold">Monitored Sites</h2>
            <p className="text-sm text-gray-600 mt-1">
              {sites.length} site{sites.length !== 1 ? 's' : ''} being monitored
            </p>
          </div>
          
          <div className="flex-1 overflow-auto">
            <SitesList
              sites={sites}
              selectedSite={selectedSite}
              onSiteSelect={setSelectedSite}
              onSiteDeleted={handleSiteDeleted}
            />
          </div>
        </div>

        {/* Right Panel - Status Details */}
        <div className="flex-1 flex flex-col">
          {selectedSite ? (
            <StatusPanel site={selectedSite} />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Site Selected
                </h3>
                <p className="text-gray-600">
                  {sites.length === 0
                    ? "Add your first site to start monitoring"
                    : "Select a site from the sidebar to view its status"
                  }
                </p>
                {sites.length === 0 && (
                  <Button className="mt-4" onClick={() => setIsAddDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Your First Site
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Site Dialog */}
      <AddSiteDialog
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
        onSiteAdded={handleSiteAdded}
      />
    </div>
  );
} 