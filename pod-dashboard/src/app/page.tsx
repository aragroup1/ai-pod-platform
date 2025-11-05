"use client";

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { 
  DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, RefreshCw, 
  Zap, Info, Brain, Image as ImageIcon, ExternalLink, LayoutGrid, 
  Check, X, Trash2, Rocket, Calendar, Settings, Target, Package, ThumbsUp, ThumbsDown,
  Database
} from 'lucide-react';
import { Toaster, toast } from 'sonner';

// CRITICAL: Hardcoded HTTPS URL
const API_BASE_URL = 'https://backend-production-7aae.up.railway.app/api/v1';

// Interfaces
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
  const [isLoadingKeywords, setIsLoadingKeywords] = useState(false);
  const [showGallery, setShowGallery] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  
  const hiddenProductIds = useRef<Set<number>>(new Set());
  const fetchInProgress = useRef(false);
  
  const [budgetMode, setBudgetMode] = useState<'cheap' | 'balanced' | 'quality'>('balanced');
  const [testingMode, setTestingMode] = useState(true);
  const [trendsToGenerate, setTrendsToGenerate] = useState(10);
  const [dailyGenerationTarget, setDailyGenerationTarget] = useState(100);
  const [autoGeneration, setAutoGeneration] = useState(false);

  // Fetch dashboard data with deduplication
  const fetchData = async () => {
    if (fetchInProgress.current) {
      console.log('⏭️ Fetch already in progress, skipping...');
      return;
    }
    
    fetchInProgress.current = true;
    console.log('🔍 Fetching from API:', API_BASE_URL);

    try {
      setLoading(true);
      setError(null);

      const [statsResponse, productsResponse, genStatusResponse, analyticsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/analytics/dashboard`).catch(err => {
          console.error('Stats fetch failed:', err);
          return null;
        }),
        fetch(`${API_BASE_URL}/products?limit=100&status=active&include_images=true`).catch(err => {
          console.error('Products fetch failed:', err);
          throw err;
        }),
        fetch(`${API_BASE_URL}/generation/status`).catch(err => {
          console.error('Gen status fetch failed:', err);
          return null;
        }),
        fetch(`${API_BASE_URL}/trends/analytics`).catch(err => {
          console.error('Analytics fetch failed:', err);
          return null;
        })
      ]);

      console.log('✅ Responses received');

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
        const visibleProducts = (productsData.products || []).filter(
          (p: Product) => 
            p.status !== 'rejected' && 
            p.status !== 'approved' &&
            !hiddenProductIds.current.has(p.id)
        );
        setRecentProducts(visibleProducts);
      }
      
      if (genStatusResponse?.ok) {
        const genData = await genStatusResponse.json();
        setGenStatus(genData);
      }
      
      if (analyticsResponse?.ok) {
        const analyticsData = await analyticsResponse.json();
        setTrendAnalytics(analyticsData);
      }

    } catch (err: any) {
      console.error("❌ Fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
      fetchInProgress.current = false;
    }
  };

  const approveProduct = async (productId: number) => {
    try {
      hiddenProductIds.current.add(productId);
      setRecentProducts(prev => prev.filter(p => p.id !== productId));
      
      const response = await fetch(`${API_BASE_URL}/product-feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          action: 'approve'
        })
      });

      if (!response.ok) {
        hiddenProductIds.current.delete(productId);
        await fetchData();
        throw new Error('Approval failed');
      }

      toast.success(`Product approved for Shopify!`, {
        icon: <Check className="h-4 w-4" />
      });
      
    } catch (err: any) {
      toast.error(`Approval failed: ${err.message}`);
    }
  };

  const rejectProduct = async (productId: number) => {
    try {
      hiddenProductIds.current.add(productId);
      setRecentProducts(prev => prev.filter(p => p.id !== productId));
      
      const response = await fetch(`${API_BASE_URL}/product-feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          action: 'reject'
        })
      });

      if (!response.ok) {
        hiddenProductIds.current.delete(productId);
        await fetchData();
        throw new Error('Rejection failed');
      }
      
      toast.success(`Product rejected and deleted from S3`, {
        icon: <ThumbsDown className="h-4 w-4" />
      });
      
    } catch (err: any) {
      toast.error(`Rejection failed: ${err.message}`);
    }
  };

  const loadInitialKeywords = async () => {
    setIsLoadingKeywords(true);
    toast.info("🚀 Loading initial keyword database (1,250+ keywords)...");

    try {
      const response = await fetch(`${API_BASE_URL}/trends/load-initial-keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) throw new Error('Failed to load keywords');

      const data = await response.json();
      
      if (data.success) {
        toast.success(
          `✅ Loaded ${data.keywords_loaded} keywords across ${data.categories} categories! Ready for ${data.expected_skus} SKUs`,
          { duration: 10000 }
        );
        setTimeout(fetchData, 2000);
      } else {
        toast.error(data.message || "Load failed");
      }

    } catch (err: any) {
      toast.error(`Keyword load failed: ${err.message}`);
    } finally {
      setIsLoadingKeywords(false);
    }
  };

  const launch10KInitial = async () => {
    setIsLaunching10K(true);
    toast.info("🚀 Launching 10K initial keyword strategy...");

    try {
      const response = await fetch(`${API_BASE_URL}/trends/fetch-10k-initial`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to launch 10K strategy');

      const data = await response.json();
      
      if (data.success) {
        toast.success(
          `10K Strategy Launched! ${data.keywords_stored} keywords stored. Total designs: ${data.total_designs_planned}`,
          { duration: 10000 }
        );
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

  const fetchTrends = async () => {
    setIsFetchingTrends(true);
    toast.info("🔍 Fetching trending keywords...");

    try {
      const response = await fetch(`${API_BASE_URL}/trends/fetch?region=GB&limit=20`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to fetch trends');

      const data = await response.json();
      
      if (data.success) {
        toast.success(`${data.message} - ${data.trends_stored} keywords stored`, { duration: 5000 });
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

  const calculateDailyGeneration = () => {
    const trendsPerDay = Math.ceil(dailyGenerationTarget / 8);
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

  const generateProducts = async (customTrendCount?: number) => {
    const trendsCount = customTrendCount || trendsToGenerate;
    setIsGenerating(true);
    
    const modeLabel = testingMode ? 'Testing' : budgetMode;
    toast.info(`Starting generation: ${trendsCount * 8} products (${modeLabel} mode)...`);

    try {
      const response = await fetch(`${API_BASE_URL}/generation/batch-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      toast.success(`Generating ${data.expected_products} products! Cost: ${data.estimated_cost}`, { duration: 8000 });
      
      setTimeout(fetchData, 10000);
      setTimeout(fetchData, 30000);
      setTimeout(fetchData, 60000);

    } catch (err: any) {
      toast.error(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Initial fetch and polling
  useEffect(() => {
    fetchData();
    
    const pollInterval = setInterval(() => {
      if (!isGenerating && !fetchInProgress.current) {
        fetchData();
      }
    }, 30000);
    
    return () => clearInterval(pollInterval);
  }, [isGenerating]);

  // Auto-generation polling
  useEffect(() => {
    if (autoGeneration && !isGenerating && genStatus) {
      const interval = setInterval(() => {
        const dailyCalc = calculateDailyGeneration();
        if ((genStatus.total_products % dailyGenerationTarget) === 0) {
          generateProducts(dailyCalc.trendsNeeded);
        }
      }, 3600000);
      
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

  const visibleProducts = recentProducts.filter(p => !hiddenProductIds.current.has(p.id));
  const productsWithImages = visibleProducts.filter(p => p.artwork?.image_url);
  const dailyCalc = calculateDailyGeneration();

  const progressData = [
    { name: 'Current', designs: genStatus?.total_products || 0 },
    { name: '10K Goal', designs: 10000 },
    { name: '50K Goal', designs: 50000 }
  ];

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-muted/40">
      <Toaster richColors position="bottom-left" />
      
      <div className="w-full max-w-7xl space-y-6">
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
            <Button onClick={fetchData} variant="outline" disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => setShowSettings(!showSettings)} variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
            <Button onClick={() => setShowGallery(!showGallery)} variant={showGallery ? "default" : "outline"}>
              <LayoutGrid className="h-4 w-4 mr-2" />
              Gallery ({productsWithImages.length})
            </Button>
          </div>
        </header>

        {showSettings && (
          <Card className="border-orange-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Daily Generation Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Daily Target</label>
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
                  <p><strong>10K in:</strong> {dailyCalc.daysTo10K} days</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {(trendAnalytics?.total_trends || 0) === 0 && !showGallery && (
          <Card className="border-blue-500 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-600" />
                No Keywords Found - Load Initial Database
              </CardTitle>
              <CardDescription>
                Start by loading 1,250+ curated keywords across 74 categories
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <h4 className="font-semibold">Quick Start:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• 1,250+ proven keywords</li>
                    <li>• 74 trending categories</li>
                    <li>• ~10,000 unique designs</li>
                    <li>• Instant database load</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold">Categories Include:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Nature & Landscapes</li>
                    <li>• Typography & Quotes</li>
                    <li>• Abstract & Geometric</li>
                    <li>• Animals, Holidays, Cities...</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold">Ready to Launch:</h4>
                  <p className="text-sm">Click below to load keywords into your database</p>
                  <Button 
                    onClick={loadInitialKeywords}
                    disabled={isLoadingKeywords}
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600"
                  >
                    {isLoadingKeywords ? (
                      <>
                        <Database className="h-4 w-4 mr-2 animate-pulse" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <Database className="h-4 w-4 mr-2" />
                        Load 1,250+ Keywords
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {(genStatus?.total_products || 0) < 1000 && (trendAnalytics?.total_trends || 0) > 0 && !showGallery && (
          <Card className="border-purple-500 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Rocket className="h-5 w-5 text-purple-600" />
                10K Initial Launch Strategy
              </CardTitle>
              <CardDescription>
                Fast-track your inventory with comprehensive keyword expansion
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <h4 className="font-semibold">What You'll Get:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Expanded keyword database</li>
                    <li>• Multiple categories</li>
                    <li>• Volume-based allocation</li>
                    <li>• Ready for generation</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold">Categories:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Nature & Landscapes</li>
                    <li>• Typography & Quotes</li>
                    <li>• Abstract & Geometric</li>
                    <li>• Plus many more...</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold">Launch Strategy:</h4>
                  <p className="text-sm">Automated keyword expansion</p>
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
                  <p>No products to display</p>
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
                              <Button 
                                size="sm" 
                                className="h-6 w-6 p-0"
                                onClick={() => approveProduct(product.id)}
                                title="Approve for Shopify"
                              >
                                <Check className="h-3 w-3" />
                              </Button>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                className="h-6 w-6 p-0"
                                onClick={() => rejectProduct(product.id)}
                                title="Reject (won't show again)"
                              >
                                <X className="h-3 w-3" />
                              </Button>
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
