"use client";

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  AlertCircle, RefreshCw, Zap, Brain, Image as ImageIcon, LayoutGrid, 
  Check, X, Rocket, Calendar, Settings, Target, Package, ThumbsUp, ThumbsDown, Database
} from 'lucide-react';
import { Toaster, toast } from 'sonner';

const API_BASE_URL = 'https://backend-production-7aae.up.railway.app/api/v1';

// Interfaces (keeping them the same)
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
}

interface Product {
  id: number;
  title: string;
  sku: string;
  status: string;
  base_price: number;
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
  goal_progress: {
    current_designs: number;
    progress_percentage: number;
  };
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentProducts, setRecentProducts] = useState<Product[]>([]);
  const [genStatus, setGenStatus] = useState<GenerationStatus | null>(null);
  const [trendAnalytics, setTrendAnalytics] = useState<TrendAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingKeywords, setIsLoadingKeywords] = useState(false);
  const [showGallery, setShowGallery] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  
  const hiddenProductIds = useRef<Set<number>>(new Set());
  const fetchInProgress = useRef(false);
  const lastFetchTime = useRef(0);
  
  const [testingMode, setTestingMode] = useState(true);
  const [trendsToGenerate, setTrendsToGenerate] = useState(10);

  // OPTIMIZED: Debounced fetch with rate limiting
  const fetchData = async () => {
    const now = Date.now();
    
    // Rate limit: Don't fetch more than once every 5 seconds
    if (fetchInProgress.current || (now - lastFetchTime.current < 5000)) {
      console.log('⏭️ Fetch skipped (rate limited)');
      return;
    }
    
    fetchInProgress.current = true;
    lastFetchTime.current = now;

    try {
      setLoading(true);
      setError(null);

      // Fetch analytics and gen status in parallel
      const [analyticsResponse, genStatusResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/trends/analytics`).catch(() => null),
        fetch(`${API_BASE_URL}/generation/status`).catch(() => null)
      ]);

      if (analyticsResponse?.ok) {
        const data = await analyticsResponse.json();
        setTrendAnalytics(data);
        setStats({
          revenue: 0,
          orders: 0,
          products: data.goal_progress?.current_designs || 0,
          trends: data.total_trends || 0
        });
      }
      
      if (genStatusResponse?.ok) {
        const data = await genStatusResponse.json();
        setGenStatus(data);
      }

      // Only fetch products if showing gallery
      if (showGallery) {
        const productsResponse = await fetch(`${API_BASE_URL}/products?limit=50&status=active`);
        if (productsResponse?.ok) {
          const data = await productsResponse.json();
          const visible = (data.products || []).filter(
            (p: Product) => !hiddenProductIds.current.has(p.id)
          );
          setRecentProducts(visible);
        }
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
      
      await fetch(`${API_BASE_URL}/product-feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, action: 'approve' })
      });

      toast.success('Product approved!', { icon: <Check className="h-4 w-4" /> });
    } catch (err: any) {
      toast.error(`Failed: ${err.message}`);
    }
  };

  const rejectProduct = async (productId: number) => {
    try {
      hiddenProductIds.current.add(productId);
      setRecentProducts(prev => prev.filter(p => p.id !== productId));
      
      await fetch(`${API_BASE_URL}/product-feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, action: 'reject' })
      });
      
      toast.success('Product rejected', { icon: <ThumbsDown className="h-4 w-4" /> });
    } catch (err: any) {
      toast.error(`Failed: ${err.message}`);
    }
  };

  const loadInitialKeywords = async () => {
    setIsLoadingKeywords(true);
    toast.info("🚀 Loading keywords...");

    try {
      const response = await fetch(`${API_BASE_URL}/trends/load-initial-keywords`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed');

      const data = await response.json();
      toast.success(`✅ Loaded ${data.keywords_loaded} keywords!`, { duration: 8000 });
      setTimeout(fetchData, 3000);
    } catch (err: any) {
      toast.error(`Failed: ${err.message}`);
    } finally {
      setIsLoadingKeywords(false);
    }
  };

  const generateProducts = async (customCount?: number) => {
    const count = customCount || trendsToGenerate;
    setIsGenerating(true);
    toast.info(`Generating ${count * 8} products...`);

    try {
      const response = await fetch(`${API_BASE_URL}/generation/batch-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          limit: count,
          min_trend_score: 6.0,
          testing_mode: testingMode,
          budget_mode: 'balanced'
        })
      });

      if (!response.ok) throw new Error('Generation failed');

      const data = await response.json();
      toast.success(`Generating ${data.expected_products} products!`, { duration: 8000 });
      
      // Refresh after generation completes
      setTimeout(fetchData, 15000);
    } catch (err: any) {
      toast.error(`Failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Initial fetch only
  useEffect(() => {
    fetchData();
  }, []);

  // Fetch when gallery opens
  useEffect(() => {
    if (showGallery) {
      fetchData();
    }
  }, [showGallery]);

  // Poll every 60 seconds if generating
  useEffect(() => {
    if (isGenerating) {
      const interval = setInterval(fetchData, 60000);
      return () => clearInterval(interval);
    }
  }, [isGenerating]);

  if (error && !stats) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center p-8">
          <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
          <h2 className="mt-4 text-2xl font-bold">Connection Error</h2>
          <p className="mt-2">{error}</p>
          <Button onClick={fetchData} className="mt-6">Retry</Button>
        </div>
      </div>
    );
  }

  const productsWithImages = recentProducts.filter(p => p.artwork?.image_url);

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-muted/40">
      <Toaster richColors position="bottom-right" />
      
      <div className="w-full max-w-7xl space-y-6">
        <header className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              AI POD Dashboard
            </h1>
            <p className="text-muted-foreground">
              {trendAnalytics?.goal_progress.current_designs || 0} / 10,000 designs
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={fetchData} variant="outline" disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => setShowGallery(!showGallery)} variant={showGallery ? "default" : "outline"}>
              <LayoutGrid className="h-4 w-4 mr-2" />
              Gallery ({productsWithImages.length})
            </Button>
          </div>
        </header>

        {(trendAnalytics?.total_trends || 0) === 0 && (
          <Card className="border-blue-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Load Initial Keywords
              </CardTitle>
              <CardDescription>1,250+ keywords across 74 categories</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={loadInitialKeywords}
                disabled={isLoadingKeywords}
                className="bg-gradient-to-r from-blue-600 to-indigo-600"
              >
                {isLoadingKeywords ? 'Loading...' : 'Load Keywords'}
              </Button>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Products</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{genStatus?.total_products || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Keywords</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{trendAnalytics?.total_trends || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Ready</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{genStatus?.trends_awaiting_generation || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {trendAnalytics?.goal_progress.progress_percentage || 0}%
              </div>
            </CardContent>
          </Card>
        </div>

        {showGallery ? (
          <Card>
            <CardHeader>
              <CardTitle>Product Gallery</CardTitle>
            </CardHeader>
            <CardContent>
              {productsWithImages.length === 0 ? (
                <div className="text-center py-12">
                  <ImageIcon className="h-16 w-16 mx-auto mb-4 opacity-20" />
                  <p>No products yet</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
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
                            <ImageIcon className="h-8 w-8 opacity-20" />
                          </div>
                        )}
                      </div>
                      <CardContent className="p-2">
                        <p className="text-xs truncate mb-1">{product.title}</p>
                        <div className="flex gap-1">
                          <Button size="sm" className="h-6 w-full p-0" onClick={() => approveProduct(product.id)}>
                            <Check className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="destructive" className="h-6 w-full p-0" onClick={() => rejectProduct(product.id)}>
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Generation Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <div>
                  <label className="text-sm mb-2 block">Mode</label>
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
                  <label className="text-sm mb-2 block">Batch</label>
                  <div className="flex gap-1">
                    {[5, 10, 20].map(num => (
                      <Button
                        key={num}
                        variant={trendsToGenerate === num ? "default" : "outline"}
                        onClick={() => setTrendsToGenerate(num)}
                        size="sm"
                      >
                        {num}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
              
              <Button 
                onClick={() => generateProducts()}
                disabled={isGenerating || (genStatus?.trends_awaiting_generation || 0) === 0}
                className="w-full"
              >
                <Zap className={`h-4 w-4 mr-2 ${isGenerating ? 'animate-pulse' : ''}`} />
                Generate {trendsToGenerate * 8} Products
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}
