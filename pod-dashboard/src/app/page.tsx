"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, Play, RefreshCw, Zap, Info, Brain, Image as ImageIcon, ExternalLink } from 'lucide-react';
import { Toaster, toast } from 'sonner';
import Image from 'next/image';

// --- Data Interfaces ---
interface DashboardStats {
  revenue: number;
  orders: number;
  products: number;
  trends: number;
}

interface Artwork {
  image_url: string | null;
  style: string | null;
  provider: string | null;
  quality_score: number;
  model_used: string | null;
}

interface Product {
  id: number;
  title: string;
  sku: string;
  status: string;
  base_price: number;
  description?: string;
  artwork?: Artwork | null;
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
  const [activeTab, setActiveTab] = useState("dashboard");
  
  // Generation settings
  const [budgetMode, setBudgetMode] = useState<'cheap' | 'balanced' | 'quality'>('balanced');
  const [testingMode, setTestingMode] = useState(false);

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
        fetch(`${API_URL}/api/v1/products/?limit=20`, {
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
        `Cost Estimate: ${data.total_products} products = ${data.estimated_total_cost}`,
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
    toast.info(`Starting generation in ${modeLabel} mode...`);

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
        `Generating ${data.expected_products} products! Cost: ${data.estimated_cost}`,
        { duration: 8000 }
      );
      
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

  // Filter products with images
  const productsWithImages = recentProducts.filter(p => p.artwork?.image_url);

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-muted/40">
      <Toaster richColors position="top-right" />
      
      <div className="w-full max-w-7xl space-y-6">
        {/* Header */}
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
          </div>
        </header>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="gallery">
              <ImageIcon className="h-4 w-4 mr-2" />
              Gallery ({productsWithImages.length})
            </TabsTrigger>
            <TabsTrigger value="generate">Generate</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-4">
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
                    {productsWithImages.length} with images
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

            {/* Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue Overview</CardTitle>
              </CardHeader>
              <CardContent className="pl-2">
                <ResponsiveContainer width="100%" height={300}>
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
          </TabsContent>

          {/* Gallery Tab */}
          <TabsContent value="gallery" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Product Gallery</CardTitle>
                <CardDescription>
                  View all generated artwork ({productsWithImages.length} products with images)
                </CardDescription>
              </CardHeader>
              <CardContent>
                {productsWithImages.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <ImageIcon className="h-16 w-16 mx-auto mb-4 opacity-20" />
                    <p>No products with images yet.</p>
                    <p className="text-sm mt-2">Generate some products to see them here!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {productsWithImages.map((product) => (
                      <div key={product.id} className="group relative">
                        <div className="aspect-square relative rounded-lg overflow-hidden border bg-muted">
                          {product.artwork?.image_url ? (
                            <div className="relative h-full w-full">
                              <img
                                src={product.artwork.image_url}
                                alt={product.title}
                                className="object-cover w-full h-full"
                              />
                              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-4 text-white text-center">
                                <p className="text-sm font-semibold mb-2">{product.title}</p>
                                <Badge variant="secondary" className="mb-2">
                                  {product.artwork.style}
                                </Badge>
                                <p className="text-xs">£{product.base_price}</p>
                                <a
                                  href={product.artwork.image_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="mt-2 text-xs underline flex items-center gap-1"
                                >
                                  View Full <ExternalLink className="h-3 w-3" />
                                </a>
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-center justify-center h-full">
                              <ImageIcon className="h-12 w-12 text-muted-foreground/20" />
                            </div>
                          )}
                        </div>
                        <div className="mt-2">
                          <p className="text-xs font-medium truncate">{product.title}</p>
                          <div className="flex items-center justify-between mt-1">
                            <Badge variant="outline" className="text-xs">
                              {product.artwork?.style}
                            </Badge>
                            <span className="text-xs font-semibold">£{product.base_price}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Generate Tab */}
          <TabsContent value="generate" className="space-y-4">
            {/* Generation Controls */}
            {genStatus && genStatus.trends_awaiting_generation > 0 ? (
              <Card className="border-primary">
                <CardHeader>
                  <CardTitle>Generate Products with Intelligent AI</CardTitle>
                  <CardDescription>
                    {genStatus.trends_awaiting_generation} trends ready • System automatically chooses best model
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
                  
                  <div className="text-sm text-muted-foreground space-y-1 bg-muted p-4 rounded-lg">
                    <p className="font-semibold mb-2">Cost Guide:</p>
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
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <AlertCircle className="h-16 w-16 mx-auto mb-4 text-muted-foreground/20" />
                  <h3 className="text-lg font-semibold mb-2">No Trends Available</h3>
                  <p className="text-muted-foreground mb-4">
                    Fetch some trends first to start generating products
                  </p>
                  <Button onClick={fetchTrends} disabled={isFetchingTrends}>
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Fetch Trends Now
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Model Info */}
            {modelInfo && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Intelligent AI Model Selection
                  </CardTitle>
                  <CardDescription>
                    System automatically selects the best AI model for each art style
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(modelInfo.models).map(([key, model]: [string, any]) => (
                      <div key={key} className="p-3 bg-muted rounded-lg">
                        <h4 className="font-semibold text-sm mb-2 capitalize">{key.replace('-', ' ')}</h4>
                        <div className="text-xs space-y-1 text-muted-foreground">
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
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
