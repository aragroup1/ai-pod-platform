"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { 
  DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, RefreshCw, 
  Zap, Info, Brain, Image as ImageIcon, ExternalLink, LayoutGrid, 
  Check, X, Trash2, Rocket, Calendar, Settings, Target, Package
} from 'lucide-react';
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

interface TrendAnalytics {
  total_trends: number;
  total_categories: number;
  avg_trend_score: number;
  goal_progress: {
    target_designs: number;
    current_designs: number;
    designs_needed: number;
    trends_needed: number;
    progress_percentage: number;
  };
  top_categories: Array<{
    name: string;
    count: number;
    avg_score: number;
  }>;
}

// --- Main Dashboard Component ---
export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentProducts, setRecentProducts] = useState<Product[]>([]);
  const [genStatus, setGenStatus] = useState<GenerationStatus | null>(null);
  const [trendAnalytics, setTrendAnalytics] = useState<TrendAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isFetchingTrends, setIsFetchingTrends] = useState(false);
  const [isLaunching10K, setIsLaunching10K] = useState(false);
  const [showGallery, setShowGallery] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  const [rejectedProducts, setRejectedProducts] = useState<Set<number>>(new Set());
  
  // Generation settings
  const [budgetMode, setBudgetMode] = useState<'cheap' | 'balanced' | 'quality'>('balanced');
  const [testingMode, setTestingMode] = useState(true);
  const [trendsToGenerate, setTrendsToGenerate] = useState(10);
  const [dailyGenerationTarget, setDailyGenerationTarget] = useState(100); // New designs per day
  const [autoGeneration, setAutoGeneration] = useState(false);

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

      const [statsResponse, productsResponse, genStatusResponse, analyticsResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/analytics/dashboard`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => null),
        fetch(`${API_URL}/api/v1/products/?limit=100`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => null),
        fetch(`${API_URL}/api/v1/generation/status`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => null),
        fetch(`${API_URL}/api/v1/trends/analytics`, {
          headers: { 'Accept': 'application/json' }
        }).catch(e => null)
      ]);

      if (statsResponse?.ok) {
        const statsData = await statsResponse.json();
        setStats({
          revenue: statsData.revenue || 0,
          orders: statsData.orders || 0,
          products: statsData.products || 0,
          trends: statsData.trends || 0,
        });
      }
      
      if (productsResponse?.ok) {
        const productsData = await productsResponse.json();
        const filteredProducts = (productsData.products || []).filter(
          (p: Product) => !rejectedProducts.has(p.id)
        );
        setRecentProducts(filteredProducts);
      }
      
      if (genStatusResponse?.ok) {
        const genStatusData = await genStatusResponse.json();
        setGenStatus(genStatusData);
      }
      
      if (analyticsResponse?.ok) {
        const analyticsData = await analyticsResponse.json();
        setTrendAnalytics(analyticsData);
      }

    } catch (err: any) {
      console.error("Fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Launch 10K Initial Keywords
  const launch10KInitial = async () => {
    if (!API_URL) return;

    setIsLaunching10K(true);
    toast.info("🚀 Launching 10K initial keyword strategy...");

    try {
      const response = await fetch(`${API_URL}/api/v1/trends/fetch-10k-initial`, {
        method: 'POST',
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('Failed to launch 10K strategy');
      }

      const data = await response.json();
      
      if (data.success) {
        toast.success(
          <div>
            <strong>10K Strategy Launched!</strong>
            <br />
            {data.keywords_stored} keywords stored across {data.categories} categories
            <br />
            Total designs planned: {data.total_designs_planned}
            <br />
            <small>Est. cost: {data.estimated_cost.testing_mode} (test) / {data.estimated_cost.production_mode} (prod)</small>
          </div>,
          { duration: 10000 }
        );
        
        // Refresh data to show new keywords
        setTimeout(fetchData, 2000);
      } else {
        toast.error(data.message || "Launch failed");
      }

    } catch (err: any) {
      toast.error(`10K launch failed: ${err.message}`);
    } finally {
      setIsLaunching10K(false);
    }
  };

  // Fetch Trends (Regular)
  const fetchTrends = async () => {
    if (!API_URL) return;

    setIsFetchingTrends(true);
    toast.info("🔍 Fetching trending keywords...");

    try {
      const response = await fetch(`${API_URL}/api/v1/trends/fetch?region=GB&limit=20`, {
        method: 'POST',
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(errorData || 'Failed to fetch trends');
      }

      const data = await response.json();
      
      if (data.success) {
        toast.success(
          <div>
            <strong>{data.message}</strong>
            <br />
            <small>{data.trends_stored} keywords stored</small>
          </div>,
          { duration: 5000 }
        );
      } else {
        toast.warning(data.message || "No new trends found");
      }
      
      setTimeout(fetchData, 2000);

    } catch (err: any) {
      toast.error(`Trend fetch failed: ${err.message}`);
    } finally {
      setIsFetchingTrends(false);
    }
  };

  // Calculate daily generation needs
  const calculateDailyGeneration = () => {
    const trendsPerDay = Math.ceil(dailyGenerationTarget / 8); // 8 styles per trend
    const costPerDay = testingMode ? 
      (dailyGenerationTarget * 0.003) : 
      (dailyGenerationTarget * 0.04);
    
    return {
      trendsNeeded: trendsPerDay,
      dailyCost: costPerDay,
      monthlyDesigns: dailyGenerationTarget * 30,
      monthlyCost: costPerDay * 30,
      daysTo10K: Math.ceil((10000 - (genStatus?.total_products || 0)) / dailyGenerationTarget),
      daysTo50K: Math.ceil((50000 - (genStatus?.total_products || 0)) / dailyGenerationTarget)
    };
  };

  // Generate Products
  const generateProducts = async (customTrendCount?: number) => {
    if (!API_URL) return;

    const trendsCount = customTrendCount || trendsToGenerate;
    setIsGenerating(true);
    
    const modeLabel = testingMode ? 'Testing' : budgetMode;
    toast.info(`Starting generation of ${trendsCount * 8} products in ${modeLabel} mode...`);

    try {
      const response = await fetch(`${API_URL}/api/v1/generation/batch-generate`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          limit: trendsCount,
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
      
      setTimeout(fetchData, 10000);
      setTimeout(fetchData, 30000);
      setTimeout(fetchData, 60000);

    } catch (err: any) {
      toast.error(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Approve product
  const approveProduct = async (productId: number) => {
    try {
      toast.success(`Product ${productId} approved for Shopify!`);
      fetchData();
    } catch (err: any) {
      toast.error(`Approval failed: ${err.message}`);
    }
  };

  // Reject product
  const rejectProduct = async (productId: number) => {
    setRejectedProducts(prev => new Set(prev).add(productId));
    setRecentProducts(prev => prev.filter(p => p.id !== productId));
    toast.success(`Product removed from view`, {
      icon: <Trash2 className="h-4 w-4" />
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Auto-generation logic
  useEffect(() => {
    if (autoGeneration && !isGenerating && genStatus) {
      const interval = setInterval(() => {
        const dailyCalc = calculateDailyGeneration();
        if ((genStatus.total_products % dailyGenerationTarget) === 0) {
          generateProducts(dailyCalc.trendsNeeded);
        }
      }, 3600000); // Check every hour
      
      return () => clearInterval(interval);
    }
  }, [autoGeneration, isGenerating, genStatus, dailyGenerationTarget]);

  if (error && !stats) {
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

  const productsWithImages = recentProducts.filter(p => 
    p.artwork?.image_url && !rejectedProducts.has(p.id)
  );

  const dailyCalc = calculateDailyGeneration();

  // Progress chart data
  const progressData = [
    { name: 'Current', designs: genStatus?.total_products || 0 },
    { name: '10K Goal', designs: 10000 },
    { name: '50K Goal', designs: 50000 }
  ];

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
            <p className="text-muted-foreground">
              {trendAnalytics?.goal_progress.current_designs || 0} / 10,000 designs ({trendAnalytics?.goal_progress.progress_percentage || 0}%)
            </p>
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
              onClick={() => setShowSettings(!showSettings)}
              variant="outline"
            >
              <Settings className="h-4 w-4 mr-2" />
              Settings
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

        {/* Settings Panel */}
        {showSettings && (
          <Card className="border-orange-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Daily Generation Settings
              </CardTitle>
              <CardDescription>
                Configure your automated design generation strategy
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Daily Target (designs)</label>
                  <div className="flex gap-1">
                    {[50, 100, 200, 500, 1000].map(num => (
                      <Button
                        key={num}
                        variant={dailyGenerationTarget === num ? "default" : "outline"}
                        onClick={() => setDailyGenerationTarget(num)}
                        size="sm"
                        className="text-xs"
                      >
                        {num}
                      </Button>
                    ))}
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">Auto-Generation</label>
                  <Button
                    variant={autoGeneration ? "default" : "outline"}
                    onClick={() => setAutoGeneration(!autoGeneration)}
                    className="w-full"
                  >
                    {autoGeneration ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
                
                <div className="text-sm space-y-1">
                  <p><strong>Daily:</strong> {dailyCalc.trendsNeeded} trends = {dailyGenerationTarget} designs</p>
                  <p><strong>Cost:</strong> £{dailyCalc.dailyCost.toFixed(2)}/day</p>
                  <p><strong>Monthly:</strong> {dailyCalc.monthlyDesigns} designs for £{dailyCalc.monthlyCost.toFixed(2)}</p>
                  <p><strong>10K in:</strong> {dailyCalc.daysTo10K} days</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 10K Launch Card - Only show if under 1000 products */}
        {(genStatus?.total_products || 0) < 1000 && !showGallery && (
          <Card className="border-purple-500 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Rocket className="h-5 w-5 text-purple-600" />
                10K Initial Launch Strategy
              </CardTitle>
              <CardDescription>
                Fast-track your inventory with 100 proven keywords across 10 categories
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <h4 className="font-semibold">What You'll Get:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• 100 high-volume keywords</li>
                    <li>• 10 major categories</li>
                    <li>• ~10,000 unique designs</li>
                    <li>• Volume-based allocation</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold">Categories:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Nature & Landscapes</li>
                    <li>• Typography & Quotes</li>
                    <li>• Abstract & Geometric</li>
                    <li>• Animals, Botanical, Cities...</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold">Investment:</h4>
                  <p className="text-sm">Testing: ~£30</p>
                  <p className="text-sm">Production: ~£400</p>
                  <p className="text-sm">Time: ~5 hours</p>
                  <Button 
                    onClick={launch10KInitial}
                    disabled={isLaunching10K}
                    className="w-full mt-2 bg-gradient-to-r from-purple-600 to-pink-600"
                  >
                    {isLaunching10K ? (
                      <>
                        <Rocket className="h-4 w-4 mr-2 animate-pulse" />
                        Launching...
                      </>
                    ) : (
                      <>
                        <Rocket className="h-4 w-4 mr-2" />
                        Launch 10K Strategy
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Gallery View */}
        {showGallery ? (
          <Card>
            <CardHeader>
              <CardTitle>Product Gallery</CardTitle>
              <CardDescription>
                {productsWithImages.length} products • Review and approve for Shopify
              </CardDescription>
            </CardHeader>
            <CardContent>
              {productsWithImages.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <ImageIcon className="h-16 w-16 mx-auto mb-4 opacity-20" />
                  <p>No products to display.</p>
                  <p className="text-sm mt-2">Generate some products to see them here!</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
                  {productsWithImages.map((product) => (
                    <Card key={product.id} className="overflow-hidden">
                      <div className="aspect-square relative bg-muted">
                        {product.artwork?.image_url && !imageErrors.has(product.id) ? (
                          <img
                            src={product.artwork.image_url}
                            alt={product.title}
                            className="object-cover w-full h-full"
                            onError={() => setImageErrors(prev => new Set(prev).add(product.id))}
                            loading="lazy"
                          />
                        ) : (
                          <div className="flex items-center justify-center h-full">
                            <ImageIcon className="h-8 w-8 text-muted-foreground/20" />
                          </div>
                        )}
                      </div>
                      <CardContent className="p-2">
                        <div className="space-y-1">
                          <p className="text-xs font-medium truncate">{product.title}</p>
                          <div className="flex justify-between items-center">
                            <span className="text-xs font-bold">£{product.base_price}</span>
                            <div className="flex gap-1">
                              {product.status === 'active' && (
                                <>
                                  <Button 
                                    size="sm" 
                                    className="h-6 w-6 p-0"
                                    onClick={() => approveProduct(product.id)}
                                  >
                                    <Check className="h-3 w-3" />
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="destructive"
                                    className="h-6 w-6 p-0"
                                    onClick={() => rejectProduct(product.id)}
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Products</CardTitle>
                  <Package className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{genStatus?.total_products || '0'}</div>
                  <p className="text-xs text-muted-foreground">
                    {((genStatus?.total_products || 0) / 100).toFixed(1)}% to 10K
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Keywords</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{trendAnalytics?.total_trends || '0'}</div>
                  <p className="text-xs text-muted-foreground">
                    {trendAnalytics?.total_categories || 0} categories
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Ready</CardTitle>
                  <Target className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{genStatus?.trends_awaiting_generation || '0'}</div>
                  <p className="text-xs text-muted-foreground">
                    keywords to generate
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Daily Rate</CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dailyGenerationTarget}</div>
                  <p className="text-xs text-muted-foreground">
                    designs/day target
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">10K ETA</CardTitle>
                  <Rocket className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{dailyCalc.daysTo10K}d</div>
                  <p className="text-xs text-muted-foreground">
                    at current rate
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Progress Chart */}
            {trendAnalytics && (
              <Card>
                <CardHeader>
                  <CardTitle>Progress to Goals</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={progressData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="designs" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Generation Controls */}
            <Card className="border-primary">
              <CardHeader>
                <CardTitle>Product Generation Controls</CardTitle>
                <CardDescription>
                  {genStatus?.trends_awaiting_generation || 0} keywords ready • 
                  Daily target: {dailyGenerationTarget} designs
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Mode</label>
                    <div className="flex gap-2">
                      <Button
                        variant={testingMode ? "default" : "outline"}
                        onClick={() => setTestingMode(true)}
                        size="sm"
                      >
                        Test
                      </Button>
                      <Button
                        variant={!testingMode ? "default" : "outline"}
                        onClick={() => setTestingMode(false)}
                        size="sm"
                      >
                        Prod
                      </Button>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Batch Size</label>
                    <div className="flex gap-1">
                      {[5, 10, 20, 50].map(num => (
                        <Button
                          key={num}
                          variant={trendsToGenerate === num ? "default" : "outline"}
                          onClick={() => setTrendsToGenerate(num)}
                          size="sm"
                          className="text-xs px-2"
                        >
                          {num}
                        </Button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="col-span-2">
                    <label className="text-sm font-medium mb-2 block">Quick Actions</label>
                    <div className="flex gap-2">
                      <Button 
                        onClick={fetchTrends}
                        disabled={isFetchingTrends}
                        size="sm"
                        variant="secondary"
                      >
                        <TrendingUp className={`h-4 w-4 mr-1 ${isFetchingTrends ? 'animate-pulse' : ''}`} />
                        Fetch
                      </Button>
                      <Button 
                        onClick={() => generateProducts()}
                        disabled={isGenerating || (genStatus?.trends_awaiting_generation || 0) === 0}
                        size="sm"
                      >
                        <Zap className={`h-4 w-4 mr-1 ${isGenerating ? 'animate-pulse' : ''}`} />
                        Generate
                      </Button>
                      <Button 
                        onClick={() => generateProducts(dailyCalc.trendsNeeded)}
                        disabled={isGenerating}
                        size="sm"
                        variant="outline"
                      >
                        <Calendar className="h-4 w-4 mr-1" />
                        Daily ({dailyCalc.trendsNeeded})
                      </Button>
                    </div>
                  </div>
                </div>
                
                <div className="text-xs text-muted-foreground bg-muted p-3 rounded-lg grid grid-cols-2 gap-2">
                  <div>
                    <p className="font-semibold">Current Batch:</p>
                    <p>{trendsToGenerate} trends × 8 styles = {trendsToGenerate * 8} designs</p>
                    <p>Cost: £{testingMode ? (trendsToGenerate * 8 * 0.003).toFixed(2) : (trendsToGenerate * 8 * 0.04).toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="font-semibold">Daily Generation:</p>
                    <p>{dailyCalc.trendsNeeded} trends = {dailyGenerationTarget} designs</p>
                    <p>Cost: £{dailyCalc.dailyCost.toFixed(2)}/day</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}
