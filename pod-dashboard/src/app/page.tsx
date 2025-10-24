"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, Play, RefreshCw, Zap, Info, Brain } from 'lucide-react';
import { Toaster, toast } from 'sonner';

// --- Data Interfaces ---
interface DashboardStats {
  revenue: number;
  orders: number;
  products: number;
  trends: number;
}

interface Product {
  id: number;
  title: string;
  sku: string;
  status: string;
  base_price: number;
}

interface GenerationStatus {
  total_products: number;
  trends_with_products: number;
  total_artwork: number;
  trends_awaiting_generation: number;
}

interface ModelInfo {
  intelligent_selection: boolean;
  models: Record<string, any>;
  budget_modes: Record<string, any>;
}

// --- Main Dashboard Component ---
export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentProducts, setRecentProducts] = useState<Product[]>([]);
  const [genStatus, setGenStatus] = useState<GenerationStatus | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isFetchingTrends, setIsFetchingTrends] = useState(false);
  const [showModelInfo, setShowModelInfo] = useState(false);
  
  // Generation settings
  const [budgetMode, setBudgetMode] = useState<'cheap' | 'balanced' | 'quality'>('balanced');
  const [testingMode, setTestingMode] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-7aae.up.railway.app';

  // Fetch dashboard data
  const fetchData = async () => {
    if (!API_URL) {
      setError("API URL not configured");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const [statsResponse, productsResponse, genStatusResponse, modelInfoResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/analytics/dashboard`, {
          headers: { 'Accept': 'application/json' }
        }),
        fetch(`${API_URL}/api/v1/products/?limit=5`, {
          headers: { 'Accept': 'application/json' }
        }),
        fetch(`${API_URL}/api/v1/generation/status`, {
          headers: { 'Accept': 'application/json' }
        }),
        fetch(`${API_URL}/api/v1/generation/model-info`, {
          headers: { 'Accept': 'application/json' }
        })
      ]);

      if (!statsResponse.ok || !productsResponse.ok || !genStatusResponse.ok) {
        throw new Error('Failed to fetch data');
      }

      const statsData = await statsResponse.json();
      const productsData = await productsResponse.json();
      const genStatusData = await genStatusResponse.json();
      const modelInfoData = modelInfoResponse.ok ? await modelInfoResponse.json() : null;

      setStats({
        revenue: statsData.revenue || 0,
        orders: statsData.orders || 0,
        products: statsData.products || 0,
        trends: statsData.trends || 0,
      });
      
      setRecentProducts(productsData.products || []);
      setGenStatus(genStatusData);
      setModelInfo(modelInfoData);

      toast.success("Dashboard updated!");

    } catch (err: any) {
      setError(err.message);
      toast.error(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Google Trends
  const fetchTrends = async () => {
    if (!API_URL) return;

    setIsFetchingTrends(true);
    toast.info("Fetching trends from Google...");

    try {
      const response = await fetch(`${API_URL}/api/v1/trends/fetch?region=GB`, {
        method: 'POST',
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) throw new Error('Failed to fetch trends');

      const data = await response.json();
      toast.success(data.message);
      
      // Refresh dashboard after 5 seconds
      setTimeout(fetchData, 5000);

    } catch (err: any) {
      toast.error(`Trend fetch failed: ${err.message}`);
    } finally {
      setIsFetchingTrends(false);
    }
  };

  // Estimate generation cost
  const estimateCost = async () => {
    if (!API_URL) return;

    toast.info("Calculating cost estimate...");

    try {
      const response = await fetch(`${API_URL}/api/v1/generation/estimate-cost`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          limit: 2,
          min_trend_score: 6.0,
          testing_mode: testingMode,
          budget_mode: budgetMode,
          upscale: false
        })
      });

      if (!response.ok) throw new Error('Failed to estimate cost');

      const data = await response.json();
      
      toast.success(
        `Cost Estimate:\n${data.total_products} products = ${data.estimated_total_cost}\nMode: ${data.mode}`,
        { duration: 5000 }
      );

    } catch (err: any) {
      toast.error(`Estimation failed: ${err.message}`);
    }
  };

  // Generate Products
  const generateProducts = async () => {
    if (!API_URL) return;

    setIsGenerating(true);
    
    const modeLabel = testingMode ? 'Testing' : budgetMode;
    toast.info(`Starting product generation in ${modeLabel} mode...`);

    try {
      const response = await fetch(`${API_URL}/api/v1/generation/batch-generate`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          limit: 2,
          min_trend_score: 6.0,
          testing_mode: testingMode,
          budget_mode: budgetMode,
          upscale: false
        })
      });

      if (!response.ok) throw new Error('Generation failed');

      const data = await response.json();
      toast.success(
        `Generating ${data.expected_products} products!\nCost: ${data.estimated_cost}\n${data.cost_note}`,
        { duration: 8000 }
      );
      
      // Refresh dashboard after 30 seconds
      setTimeout(fetchData, 30000);

    } catch (err: any) {
      toast.error(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-background text-destructive">
        <div className="text-center p-8">
          <AlertCircle className="mx-auto h-12 w-12" />
          <h2 className="mt-4 text-2xl font-bold">Connection Error</h2>
          <p className="mt-2 text-muted-foreground">{error}</p>
          <Button onClick={fetchData} className="mt-6">Retry</Button>
        </div>
      </div>
    );
  }

  const chartData = [
    { name: 'Mon', revenue: 4000 },
    { name: 'Tue', revenue: 3000 },
    { name: 'Wed', revenue: 2000 },
    { name: 'Thu', revenue: 2780 },
    { name: 'Fri', revenue: 1890 },
    { name: 'Sat', revenue: 2390 },
    { name: 'Sun', revenue: 3490 },
  ];

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-muted/40">
      <Toaster richColors position="top-right" />
      
      <div className="w-full max-w-7xl space-y-6">
        {/* Header with Action Buttons */}
        <header className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              AI POD Dashboard
            </h1>
            <p className="text-muted-foreground">Intelligent Model Selection • Automated Print-on-Demand</p>
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={fetchData} 
              variant="outline"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button 
              onClick={fetchTrends}
              disabled={isFetchingTrends}
              variant="secondary"
            >
              <TrendingUp className={`h-4 w-4 mr-2 ${isFetchingTrends ? 'animate-pulse' : ''}`} />
              Fetch Trends
            </Button>
            <Button 
              onClick={() => setShowModelInfo(!showModelInfo)}
              variant="outline"
            >
              <Info className="h-4 w-4 mr-2" />
              Model Info
            </Button>
          </div>
        </header>

        {/* Intelligent Model Selection Info Card */}
        {showModelInfo && modelInfo && (
          <Card className="border-blue-500 bg-blue-50 dark:bg-blue-950">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Intelligent AI Model Selection
              </CardTitle>
              <CardDescription>
                System automatically selects the best AI model for each art style
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(modelInfo.models).map(([key, model]: [string, any]) => (
                  <div key={key} className="p-3 bg-background rounded-lg">
                    <h4 className="font-semibold text-sm mb-2">{key}</h4>
                    <div className="text-xs space-y-1">
                      <p>Cost: ${model.cost}</p>
                      <p>Quality: {model.quality}</p>
                      <p>Speed: {model.speed}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Generation Controls */}
        {genStatus && genStatus.trends_awaiting_generation > 0 && (
          <Card className="border-primary">
            <CardHeader>
              <CardTitle>Generate Products with Intelligent AI Selection</CardTitle>
              <CardDescription>
                {genStatus.trends_awaiting_generation} trends ready • System will automatically choose the best AI model for each style
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Mode</label>
                  <div className="flex gap-2">
                    <Button
                      variant={testingMode ? "default" : "outline"}
                      onClick={() => setTestingMode(true)}
                      size="sm"
                    >
                      Testing
                    </Button>
                    <Button
                      variant={!testingMode ? "default" : "outline"}
                      onClick={() => setTestingMode(false)}
                      size="sm"
                    >
                      Production
                    </Button>
                  </div>
                </div>
                
                {!testingMode && (
                  <div>
                    <label className="text-sm font-medium mb-2 block">Budget Mode</label>
                    <div className="flex gap-2">
                      <Button
                        variant={budgetMode === 'cheap' ? "default" : "outline"}
                        onClick={() => setBudgetMode('cheap')}
                        size="sm"
                      >
                        Cheap
                      </Button>
                      <Button
                        variant={budgetMode === 'balanced' ? "default" : "outline"}
                        onClick={() => setBudgetMode('balanced')}
                        size="sm"
                      >
                        Balanced
                      </Button>
                      <Button
                        variant={budgetMode === 'quality' ? "default" : "outline"}
                        onClick={() => setBudgetMode('quality')}
                        size="sm"
                      >
                        Quality
                      </Button>
                    </div>
                  </div>
                )}
                
                <div className="flex items-end gap-2">
                  <Button 
                    onClick={estimateCost}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <DollarSign className="h-4 w-4 mr-1" />
                    Estimate
                  </Button>
                  <Button 
                    onClick={generateProducts}
                    disabled={isGenerating}
                    size="sm"
                    className="flex-1"
                  >
                    <Zap className={`h-4 w-4 mr-1 ${isGenerating ? 'animate-pulse' : ''}`} />
                    Generate
                  </Button>
                </div>
              </div>
              
              <div className="text-sm text-muted-foreground space-y-1">
                <p>• Testing: All FLUX Schnell (~$0.024 for 8 products)</p>
                {!testingMode && (
                  <>
                    <p>• Cheap: All FLUX Schnell (~$0.024 for 8 products)</p>
                    <p>• Balanced: Smart mix (~$0.20 for 8 products) ⭐ Recommended</p>
                    <p>• Quality: Premium models (~$0.28 for 8 products)</p>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">£{stats?.revenue.toLocaleString() || '0'}</div>
              <p className="text-xs text-muted-foreground">+20.1% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Orders</CardTitle>
              <ShoppingCart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">+{stats?.orders.toLocaleString() || '0'}</div>
              <p className="text-xs text-muted-foreground">+180.1% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Products</CardTitle>
              <Palette className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{genStatus?.total_products || '0'}</div>
              <p className="text-xs text-muted-foreground">
                {genStatus?.trends_awaiting_generation || 0} trends awaiting
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Trending Topics</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.trends.toLocaleString() || '0'}</div>
              <p className="text-xs text-muted-foreground">From Google Trends</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts and Tables */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>Revenue Overview</CardTitle>
            </CardHeader>
            <CardContent className="pl-2">
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>Recent Products</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Price</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentProducts.length > 0 ? (
                    recentProducts.map(product => (
                      <TableRow key={product.id}>
                        <TableCell className="font-medium">{product.title}</TableCell>
                        <TableCell>
                          <Badge>{product.status}</Badge>
                        </TableCell>
                        <TableCell>£{product.base_price}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-muted-foreground">
                        No products yet. Click "Generate" to create some!
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
