// pod-dashboard/src/app/page.tsx - FIXED VERSION
"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { 
  DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, RefreshCw, 
  Zap, Info, Brain, Image as ImageIcon, ExternalLink, LayoutGrid, 
  Check, X, Trash2, Rocket, Calendar, Settings, Target, Package, ThumbsUp, ThumbsDown
} from 'lucide-react';
import { Toaster, toast } from 'sonner';

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
  const [showGallery, setShowGallery] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  
  // ✅ NEW: Track products being hidden to prevent flicker
  const [hiddenProducts, setHiddenProducts] = useState<Set<number>>(new Set());
  
  // Generation settings
  const [budgetMode, setBudgetMode] = useState<'cheap' | 'balanced' | 'quality'>('balanced');
  const [testingMode, setTestingMode] = useState(true);
  const [trendsToGenerate, setTrendsToGenerate] = useState(10);
  const [dailyGenerationTarget, setDailyGenerationTarget] = useState(100);
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
        fetch(`${API_URL}/api/v1/analytics/dashboard`).catch(() => null),
        fetch(`${API_URL}/api/v1/products/?limit=100&status=active&include_images=true`),
        fetch(`${API_URL}/api/v1/generation/status`).catch(() => null),
        fetch(`${API_URL}/api/v1/trends/analytics`).catch(() => null)
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
        // Filter out rejected products AND products in hiddenProducts set
        const activeProducts = (productsData.products || []).filter(
          (p: Product) => p.status !== 'rejected' && !hiddenProducts.has(p.id)
        );
        setRecentProducts(activeProducts);
      }
      
      if (genStatusResponse?.ok) {
        setGenStatus(await genStatusResponse.json());
      }
      
      if (analyticsResponse?.ok) {
        setTrendAnalytics(await analyticsResponse.json());
      }

    } catch (err: any) {
      console.error("Fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ✅ FIXED: Approve product with anti-flicker mechanism
  const approveProduct = async (productId: number) => {
    try {
      // 1. Hide immediately
      setHiddenProducts(prev => new Set(prev).add(productId));
      
      // 2. Remove from UI
      setRecentProducts(prev => prev.filter(p => p.id !== productId));
      
      // 3. Call API
      const response = await fetch(`${API_URL}/api/v1/product-feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          action: 'approve'
        })
      });

      if (!response.ok) {
        // If failed, remove from hidden set and refetch
        setHiddenProducts(prev => {
          const newSet = new Set(prev);
          newSet.delete(productId);
          return newSet;
        });
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

  // ✅ FIXED: Reject product with anti-flicker mechanism
  const rejectProduct = async (productId: number) => {
    try {
      // 1. Hide immediately (prevents flicker)
      setHiddenProducts(prev => new Set(prev).add(productId));
      
      // 2. Remove from UI
      setRecentProducts(prev => prev.filter(p => p.id !== productId));
      
      // 3. Call API
      const response = await fetch(`${API_URL}/api/v1/product-feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          action: 'reject'
        })
      });

      if (!response.ok) {
        // If failed, remove from hidden set and refetch
        setHiddenProducts(prev => {
          const newSet = new Set(prev);
          newSet.delete(productId);
          return newSet;
        });
        await fetchData();
        throw new Error('Rejection failed');
      }
      
      toast.success(`Product rejected and deleted from S3`, {
        icon: <ThumbsDown className="h-4 w-4" />
      });
      
      // Keep in hiddenProducts set permanently (or at least for this session)
      // This prevents it from reappearing even if there's a brief fetch
      
    } catch (err: any) {
      toast.error(`Rejection failed: ${err.message}`);
    }
  };

  const launch10KInitial = async () => {
    if (!API_URL) return;

    setIsLaunching10K(true);
    toast.info("🚀 Launching 10K initial keyword strategy...");

    try {
      const response = await fetch(`${API_URL}/api/v1/trends/fetch-10k-initial`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to launch 10K strategy');

      const data = await response.json();
      
      if (data.success) {
        toast.success(
          <div>
            <strong>10K Strategy Launched!</strong>
            <br />
            {data.keywords_stored} keywords stored
            <br />
            Total designs: {data.total_designs_planned}
          </div>,
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
    if (!API_URL) return;

    setIsFetchingTrends(true);
    toast.info("🔍 Fetching trending keywords...");

    try {
      const response = await fetch(`${API_URL}/api/v1/trends/fetch?region=GB&limit=20`, {
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
    if (!API_URL) return;

    const trendsCount = customTrendCount || trendsToGenerate;
    setIsGenerating(true);
    
    const modeLabel = testingMode ? 'Testing' : budgetMode;
    toast.info(`Starting generation: ${trendsCount * 8} products (${modeLabel} mode)...`);

    try {
      const response = await fetch(`${API_URL}/api/v1/generation/batch-generate`, {
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

  useEffect(() => {
    fetchData();
  }, []);

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

  // ✅ Filter out hidden products from display
  const visibleProducts = recentProducts.filter(p => !hiddenProducts.has(p.id));
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

        {/* Rest of the component remains the same... */}
        {/* I'll include the gallery section to show the change */}
        
        {showGallery && (
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
        )}
      </div>
    </main>
  );
}
