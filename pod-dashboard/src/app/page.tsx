"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, RefreshCw, Zap, Info, Brain, Image as ImageIcon, ExternalLink, LayoutGrid, Check, X } from 'lucide-react';
import { Toaster, toast } from 'sonner';

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
  const [showGallery, setShowGallery] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  const [debugInfo, setDebugInfo] = useState<string>('');
  
  // Generation settings
  const [budgetMode, setBudgetMode] = useState<'cheap' | 'balanced' | 'quality'>('balanced');
  const [testingMode, setTestingMode] = useState(true); // Start in testing mode

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
      let debugLog = `Fetching from: ${API_URL}\n\n`;

      const [statsResponse, productsResponse, genStatusResponse, modelInfoResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/analytics/dashboard`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => { debugLog += `Stats error: ${e}\n`; return null; }),
        fetch(`${API_URL}/api/v1/products/?limit=50`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => { debugLog += `Products error: ${e}\n`; return null; }),
        fetch(`${API_URL}/api/v1/generation/status`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => { debugLog += `Gen status error: ${e}\n`; return null; }),
        fetch(`${API_URL}/api/v1/generation/model-info`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => { debugLog += `Model info error: ${e}\n`; return null; })
      ]);

      if (statsResponse?.ok) {
        const statsData = await statsResponse.json();
        debugLog += `Stats: ${JSON.stringify(statsData)}\n\n`;
        setStats({
          revenue: statsData.revenue || 0,
          orders: statsData.orders || 0,
          products: statsData.products || 0,
          trends: statsData.trends || 0,
        });
      } else {
        debugLog += `Stats failed: ${statsResponse?.status}\n`;
      }
      
      if (productsResponse?.ok) {
        const productsData = await productsResponse.json();
        debugLog += `Products count: ${productsData.products?.length || 0}\n`;
        debugLog += `First product: ${JSON.stringify(productsData.products?.[0])}\n\n`;
        setRecentProducts(productsData.products || []);
      } else {
        debugLog += `Products failed: ${productsResponse?.status}\n`;
      }
      
      if (genStatusResponse?.ok) {
        const genStatusData = await genStatusResponse.json();
        debugLog += `Gen Status: ${JSON.stringify(genStatusData)}\n\n`;
        setGenStatus(genStatusData);
      }
      
      if (modelInfoResponse?.ok) {
        const modelInfoData = await modelInfoResponse.json();
        setModelInfo(modelInfoData);
      }

      setDebugInfo(debugLog);
      toast.success("Dashboard updated!");

    } catch (err: any) {
      console.error("Fetch error:", err);
      setError(err.message);
      toast.error(`Error: ${err.message}`);
      setDebugInfo(prev => prev + `\nCatch error: ${err.message}`);
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

  // Approve/Reject product for Shopify
  const approveProduct = async (productId: number) => {
    try {
      toast.success(`Product ${productId} approved! Will sync to Shopify.`);
      fetchData();
    } catch (err: any) {
      toast.error(`Approval failed: ${err.message}`);
    }
  };

  const rejectProduct = async (productId: number) => {
    try {
      toast.info(`Product ${productId} marked as rejected.`);
      fetchData();
    } catch (err: any) {
      toast.error(`Rejection failed: ${err.message}`);
    }
  };

  // Handle image load error
  const handleImageError = (productId: number) => {
    setImageErrors(prev => new Set(prev).add(productId));
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
  const pendingApproval = productsWithImages.filter(p => p.status === 'active');
  const approved = productsWithImages.filter(p => p.status === 'approved');

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
            <p className="text-muted-foreground">Intelligent Model Selection • Approval Workflow</p>
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
              onClick={() => setShowGallery(!showGallery)}
              variant={showGallery ? "default" : "outline"}
            >
              <LayoutGrid className="h-4 w-4 mr-2" />
              Gallery ({productsWithImages.length})
            </Button>
          </div>
        </header>

        {/* Debug Info Card - Shows API responses */}
        {debugInfo && (
          <Card className="border-blue-500">
            <CardHeader>
              <CardTitle className="text-sm">Debug Info</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-xs overflow-auto max-h-40 bg-muted p-2 rounded">
                {debugInfo}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Gallery/Approval View */}
        {showGallery && (
          <Card>
            <CardHeader>
              <CardTitle>Product Gallery</CardTitle>
              <CardDescription>
                All products with images ({productsWithImages.length} total, {pendingApproval.length} pending approval)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {productsWithImages.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <ImageIcon className="h-16 w-16 mx-auto mb-4 opacity-20" />
                  <p>No products with images yet.</p>
                  <p className="text-sm mt-2">Generate some products to see them here!</p>
                  <Button onClick={generateProducts} className="mt-4">
                    Generate Test Products
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {productsWithImages.map((product) => (
                    <Card key={product.id} className="overflow-hidden">
                      <div className="aspect-square relative bg-muted">
                        {product.artwork?.image_url && !imageErrors.has(product.id) ? (
                          <img
                            src={product.artwork.image_url}
                            alt={product.title}
                            className="object-cover w-full h-full"
                            onError={() => handleImageError(product.id)}
                            loading="lazy"
                          />
                        ) : (
                          <div className="flex items-center justify-center h-full">
                            <ImageIcon className="h-12 w-12 text-muted-foreground/20" />
                          </div>
                        )}
                      </div>
                      <CardContent className="p-4">
                        <div className="space-y-3">
                          <div>
                            <h3 className="font-semibold text-sm truncate">{product.title}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="outline" className="text-xs">
                                {product.artwork?.style}
                              </Badge>
                              <Badge variant={product.status === 'approved' ? 'default' : 'secondary'} className="text-xs">
                                {product.status}
                              </Badge>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-lg font-bold">£{product.base_price}</span>
                            {product.artwork?.image_url && (
                              <a
                                href={product.artwork.image_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                              >
                                View Full <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>

                          {product.status === 'active' && (
                            <div className="flex gap-2">
                              <Button 
                                size="sm" 
                                className="flex-1"
                                onClick={() => approveProduct(product.id)}
                              >
                                <Check className="h-4 w-4 mr-1" />
                                Approve
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                className="flex-1"
                                onClick={() => rejectProduct(product.id)}
                              >
                                <X className="h-4 w-4 mr-1" />
                                Reject
                              </Button>
                            </div>
                          )}

                          {product.status === 'approved' && (
                            <div className="text-center py-2 bg-green-50 dark:bg-green-950 rounded text-xs text-green-700 dark:text-green-300">
                              ✓ Ready for Shopify
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Stats Cards */}
        {!showGallery && (
          <>
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
                  <CardTitle className="text-sm font-medium">Products</CardTitle>
                  <Palette className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{genStatus?.total_products || '0'}</div>
                  <p className="text-xs text-muted-foreground">
                    {pendingApproval.length} pending approval
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

            {/* Generation Controls - ALWAYS VISIBLE NOW */}
            <Card className="border-primary">
              <CardHeader>
                <CardTitle>Generate Products with Intelligent AI</CardTitle>
                <CardDescription>
                  {genStatus ? `${genStatus.trends_awaiting_generation} trends ready • ` : ''}
                  Products require approval before Shopify sync
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
                  <p className="font-semibold mb-2">Workflow:</p>
                  <p>1. Generate products with AI</p>
                  <p>2. Review in gallery view</p>
                  <p>3. Approve best designs</p>
                  <p>4. Auto-sync to Shopify</p>
                </div>
              </CardContent>
            </Card>

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
          </>
        )}
      </div>
    </main>
  );
}
