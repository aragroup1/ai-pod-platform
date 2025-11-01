'use client';

import { useEffect, useState, useRef } from 'react';
import ProductCard from '@/components/ProductCard';
import FilterBar from '@/components/FilterBar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, Rocket, RefreshCw, Grid3x3 } from 'lucide-react';

// FIXED: Use correct backend URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-7aae.up.railway.app/api/v1';

interface Product {
  id: string;
  title: string;
  image_url?: string;
  price: number;
  category?: string;
  tags?: string[];
  artwork?: {
    id: number;
    image_url: string;
  };
}

interface GenStatus {
  trends_awaiting_generation: number;
  active_generations: number;
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingKeywords, setIsLoadingKeywords] = useState(false);
  const [isLaunching10K, setIsLaunching10K] = useState(false);
  const [showGallery, setShowGallery] = useState(false);
  const [genStatus, setGenStatus] = useState<GenStatus | null>(null);
  const hiddenProductsRef = useRef<Set<string>>(new Set());

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // FIXED: Use backend URL
      const response = await fetch(`${API_BASE_URL}/products`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // FIXED: Handle both array and object with products property
      let productsArray: Product[] = [];
      
      if (Array.isArray(data)) {
        productsArray = data;
      } else if (data.products && Array.isArray(data.products)) {
        productsArray = data.products;
      } else {
        console.error('Unexpected API response format:', data);
        throw new Error('Invalid API response format');
      }
      
      // Filter out hidden products
      const visibleProducts = productsArray.filter((p: Product) => 
        !hiddenProductsRef.current.has(String(p.id))
      );
      
      setProducts(visibleProducts);
      setFilteredProducts(visibleProducts);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load products';
      console.error('Fetch error:', err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchGenStatus = async () => {
    try {
      // FIXED: Use backend URL
      const response = await fetch(`${API_BASE_URL}/generation/status`);
      
      if (response.ok) {
        const data = await response.json();
        setGenStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch gen status:', err);
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchGenStatus();
    
    const interval = setInterval(fetchGenStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleFeedback = async (productId: string, feedback: 'approved' | 'rejected') => {
    try {
      // FIXED: Use backend URL
      const response = await fetch(`${API_BASE_URL}/product-feedback/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: parseInt(productId), action: feedback }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to submit feedback');
      }

      if (feedback === 'rejected') {
        // Immediately hide the product
        hiddenProductsRef.current.add(productId);
        setProducts(prev => prev.filter(p => String(p.id) !== productId));
        setFilteredProducts(prev => prev.filter(p => String(p.id) !== productId));
      }
    } catch (err) {
      console.error('Feedback error:', err);
      alert(`Failed to submit feedback: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleFilterChange = (filters: { 
    category?: string; 
    priceRange?: [number, number]; 
    searchTerm?: string 
  }) => {
    let filtered = [...products];

    if (filters.category && filters.category !== 'all') {
      filtered = filtered.filter(p => p.category === filters.category);
    }

    if (filters.priceRange) {
      filtered = filtered.filter(p => 
        p.price >= filters.priceRange![0] && p.price <= filters.priceRange![1]
      );
    }

    if (filters.searchTerm) {
      const term = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(p =>
        p.title?.toLowerCase().includes(term) ||
        p.tags?.some(tag => tag.toLowerCase().includes(term))
      );
    }

    setFilteredProducts(filtered);
  };

  const loadInitialKeywords = async () => {
    if (!confirm('Load 1,250+ keywords across 74 categories? This will generate ~10,000 designs.')) return;
    
    setIsLoadingKeywords(true);
    try {
      // FIXED: Use backend URL
      const response = await fetch(`${API_BASE_URL}/admin/load-keywords`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to load keywords');
      }
      
      alert(`Success! Loaded ${result.keywords_loaded || result.inserted} keywords.`);
      fetchProducts();
      fetchGenStatus();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoadingKeywords(false);
    }
  };

  const launch10KInitial = async () => {
    if (!confirm('Launch 10K strategy with 100 proven keywords across 10 major categories?')) return;
    
    setIsLaunching10K(true);
    try {
      // FIXED: Use backend URL
      const response = await fetch(`${API_BASE_URL}/trends/fetch-10k-initial`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to launch 10K');
      }
      
      alert(`Success! Loaded ${result.keywords_stored || result.inserted} keywords. Generating ~10,000 designs.`);
      fetchProducts();
      fetchGenStatus();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLaunching10K(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h2 className="text-xl font-semibold text-red-800 mb-2">Error Loading Dashboard</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <div className="text-sm text-gray-600 mb-4">
            <p>Backend URL: {API_BASE_URL}</p>
          </div>
          <Button onClick={fetchProducts} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Product Dashboard</h1>
        <Button
          onClick={() => setShowGallery(!showGallery)}
          variant="outline"
        >
          <Grid3x3 className="h-4 w-4 mr-2" />
          {showGallery ? 'Hide Gallery' : 'Show Gallery'}
        </Button>
      </div>

      {/* Keyword & Launch Section */}
      {!showGallery && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Load Keywords Card */}
          <Card className="border-blue-500 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                Load 1,250 Keywords
              </CardTitle>
              <CardDescription>
                Instant keyword database across 74 categories
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-semibold">What You Get:</h4>
                <ul className="text-sm space-y-1">
                  <li>• 1,250+ curated keywords</li>
                  <li>• 74 major categories</li>
                  <li>• ~10,000 unique designs</li>
                  <li>• Complete art coverage</li>
                </ul>
                
                <Button 
                  onClick={loadInitialKeywords}
                  disabled={isLoadingKeywords}
                  className="w-full mt-4 bg-gradient-to-r from-blue-600 to-cyan-600"
                >
                  {isLoadingKeywords ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Load Keywords
                    </>
                  )}
                </Button>
                
                {genStatus && (
                  <div className="text-xs text-muted-foreground mt-2">
                    Currently: {genStatus.trends_awaiting_generation} keywords ready
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 10K Launch Strategy Card */}
          <Card className="border-purple-500 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Rocket className="h-5 w-5 text-purple-600" />
                10K Launch Strategy
              </CardTitle>
              <CardDescription>
                Fast-track with proven keywords
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-semibold">Strategy:</h4>
                <ul className="text-sm space-y-1">
                  <li>• 100 proven keywords</li>
                  <li>• 10 major categories</li>
                  <li>• ~10,000 designs</li>
                  <li>• Volume-based allocation</li>
                </ul>
                
                <Button 
                  onClick={launch10KInitial}
                  disabled={isLaunching10K}
                  className="w-full mt-4 bg-gradient-to-r from-purple-600 to-pink-600"
                >
                  {isLaunching10K ? (
                    <>
                      <Rocket className="h-4 w-4 mr-2 animate-pulse" />
                      Launching...
                    </>
                  ) : (
                    <>
                      <Rocket className="h-4 w-4 mr-2" />
                      Launch 10K
                    </>
                  )}
                </Button>
                
                <div className="text-xs text-muted-foreground mt-2">
                  Investment: £30 test / £400 prod
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {showGallery && (
        <>
          <FilterBar onFilterChange={handleFilterChange} products={products} />
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-8">
            {filteredProducts.map(product => (
              <ProductCard
                key={product.id}
                product={{
                  id: String(product.id),
                  title: product.title,
                  image_url: product.artwork?.image_url || product.image_url || '',
                  price: product.price,
                  category: product.category,
                  tags: product.tags
                }}
                onFeedback={handleFeedback}
              />
            ))}
          </div>
          
          {filteredProducts.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              {products.length === 0 ? 'No products yet. Load keywords to generate products!' : 'No products match your filters'}
            </div>
          )}
        </>
      )}
    </main>
  );
}
