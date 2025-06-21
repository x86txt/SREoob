'use client';

import { useState, useEffect } from 'react';
import { getSitesStatus } from '@/lib/api';
import { type SiteStatus } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Server, Crown, Lock, Shield, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function AgentsPage() {
  const [agents, setAgents] = useState<SiteStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const allSites = await getSitesStatus();
        const agentSites = allSites.filter(site => {
          const url = site.url || '';
          const name = site.name || '';
          return (
            url.includes(':8081') || 
            url.toLowerCase().includes('agent') || 
            name.toLowerCase().includes('agent') ||
            site.connection_type === 'agent'
          );
        });
        
        // Create master/controller node if no agents exist
        const masterNode = {
          id: -1, // Special ID for master
          name: 'Controller (Master)',
          url: window.location.origin,
          connection_type: 'controller' as const,
          status: 'up',
          response_time: 0.001,
          hostname: window.location.hostname,
          ip_address: '127.0.0.1', // Localhost for master
          protocol: window.location.protocol.replace(':', ''),
          is_encrypted: window.location.protocol === 'https:',
          connection_status: 'connected' as const,
          checked_at: new Date().toISOString(),
          total_up: 1,
          total_down: 0,
          created_at: new Date().toISOString(),
        };

        const displayNodes = agentSites.length > 0 ? agentSites : [masterNode];
        setAgents(displayNodes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch agents');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getStatusBadge = (status: string, connectionStatus?: string) => {
    if (connectionStatus === 'connected') {
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Connected</Badge>;
    }
    switch (status) {
      case 'up':
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Online</Badge>;
      case 'down':
        return <Badge variant="destructive">Down</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const getProtocolBadge = (site: SiteStatus) => {
    const protocol = site.protocol?.toUpperCase() || 'UNKNOWN';
    const isEncrypted = site.is_encrypted;
    
    return (
      <div className="flex items-center space-x-1">
        <Badge 
          variant={isEncrypted ? "default" : "secondary"}
          className={cn(isEncrypted && "bg-green-100 text-green-800 border-green-300")}
        >
          {protocol}
        </Badge>
        {isEncrypted && <Lock className="h-3 w-3 text-yellow-500" />}
        {site.fallback_used && <Shield className="h-3 w-3 text-orange-500" />}
      </div>
    );
  };

  const formatResponseTime = (time?: number) => {
    if (time === undefined || time === null) return 'N/A';
    return `${Math.round(time * 1000)}ms`;
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6 animate-pulse text-primary" />
          <span className="text-lg">Loading Agent Data...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <header className="border-b bg-card px-6 py-4">
        <div>
          <h1 className="text-2xl font-semibold">Agents</h1>
          <p className="text-muted-foreground">
            A list of your registered monitoring agents.
          </p>
        </div>
      </header>
      <main className="p-6 space-y-6">
        {error && (
          <Card className="border-destructive bg-destructive/10">
            <CardContent className="p-4"><p className="text-destructive">{error}</p></CardContent>
          </Card>
        )}
        <Card>
          <CardHeader>
            <CardTitle>Registered Agents</CardTitle>
            <CardDescription>
              These are the distributed agents reporting monitoring data.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <div className="grid grid-cols-12 gap-4 p-4 font-medium text-sm bg-muted/50 border-b">
                <div className="col-span-4">Agent Name</div>
                <div className="col-span-2">IP Address</div>
                <div className="col-span-2">Protocol</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-2">Response Time</div>
              </div>
              {agents.length === 0 && !loading && (
                <div className="p-8 text-center text-muted-foreground">No agents found.</div>
              )}
              <div className="divide-y">
                {agents.map((agent) => (
                  <div key={agent.id} className="grid grid-cols-12 gap-4 p-4 items-center hover:bg-muted/50">
                    <div className="col-span-4 flex items-center">
                      {agent.id === -1 ? (
                        <Crown className="h-4 w-4 text-yellow-600 mr-2" />
                      ) : (
                        <Server className="h-4 w-4 text-blue-600 mr-2" />
                      )}
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-sm text-muted-foreground flex items-center">
                          {agent.url}
                          <a href={agent.url} target="_blank" rel="noopener noreferrer" className="ml-2 text-primary hover:text-primary/80">
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </div>
                      </div>
                    </div>
                    <div className="col-span-2">{agent.ip_address || 'N/A'}</div>
                    <div className="col-span-2">{getProtocolBadge(agent)}</div>
                    <div className="col-span-2">{getStatusBadge(agent.status || 'unknown', agent.connection_status)}</div>
                    <div className="col-span-2">{formatResponseTime(agent.response_time)}</div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </>
  );
} 