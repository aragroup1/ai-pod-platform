"use client";
import { 
  ShoppingBag, Upload, Settings, CheckCircle, XCircle, 
  ExternalLink, Image as ImageIcon, FileText, Edit, Home  // ← Add Home
} from 'lucide-react';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend2-production-c1d4.up.railway.app/api/v1';

interface Product {
  id: number;
  title: string;
  sku: string;
  description: string;
  base_price: number;
  status: string;
  artwork?: {
    image_url: string;
    style: string;
    quality_score: number;
  };
  created_at: string;
}

interface ShopifyConfig {
  shop_url: string;
  access_token: string;
  api_key: string;
}

export default function ShopifyQueue() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<number | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  
  // Shopify config
  const [config, setConfig] = useState<ShopifyConfig>({
    shop_url: '',
    access_token: '',
    api_key: ''
  });

  const fetchApprovedProducts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/products?status=approved&limit=100`);
      const data = await res.json();
      setProducts(data.products || []);
    } catch (err) {
      toast.error('Failed to load approved products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovedProducts();
  }, []);

  const uploadToShopify = async (productId: number) => {
    setUploading(productId);
    try {
      const res = await fetch(`${API_BASE_URL}/shopify/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
      });

      if (res.ok) {
        const data = await res.json();
        toast.success('Product uploaded to Shopify!');
        console.log('Shopify response:', data);
        // Remove from queue
        setProducts(prev => prev.filter(p => p.id !== productId));
      } else {
        const error = await res.json();
        toast.error(`Upload failed: ${error.detail || 'Unknown error'}`);
        console.error('Upload error:', error);
      }
    } catch (err: any) {
      toast.error(`Upload error: ${err.message}`);
      console.error('Upload error:', err);
    } finally {
      setUploading(null);
    }
  };

  const uploadAllToShopify = async () => {
    if (products.length === 0) {
      toast.error('No products to upload');
      return;
    }

    toast.info(`Uploading ${products.length} products...`);
    
    for (const product of products) {
      await uploadToShopify(product.id);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    toast.success('Batch upload complete!');
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading queue...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <ShoppingBag className="h-8 w-8" />
            Shopify Upload Queue
          </h1>
          <p className="text-muted-foreground mt-1">
            {products.length} products ready for upload
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => window.location.href = '/'}>
  <Home className="h-4 w-4 mr-2" />
  Dashboard
</Button>
          <Button onClick={async () => {
  toast.info('Generating SEO for all products...');
  await fetch(`${API_BASE_URL}/product-feedback/batch-generate-seo`, {method: 'POST'});
  toast.success('SEO generated!');
  fetchApprovedProducts();
}}>
  Regenerate All SEO
</Button>
          <Button 
            variant="outline"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          <Button 
            onClick={uploadAllToShopify}
            disabled={products.length === 0 || uploading !== null}
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload All ({products.length})
          </Button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Shopify Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Shop URL</label>
              <Input
                placeholder="your-store.myshopify.com"
                value={config.shop_url}
                onChange={(e) => setConfig({...config, shop_url: e.target.value})}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Access Token</label>
              <Input
                type="password"
                placeholder="shpat_..."
                value={config.access_token}
                onChange={(e) => setConfig({...config, access_token: e.target.value})}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">API Key (optional)</label>
              <Input
                placeholder="API Key"
                value={config.api_key}
                onChange={(e) => setConfig({...config, api_key: e.target.value})}
              />
            </div>
            <Button 
              onClick={() => {
                toast.success('Settings saved!');
                setShowSettings(false);
              }}
            >
              Save Configuration
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Products Grid */}
      {products.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <ShoppingBag className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Products in Queue</h3>
            <p className="text-muted-foreground">
              Approve products from the dashboard to add them here.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {products.map((product) => (
            <Card key={product.id} className="overflow-hidden">
              <div className="grid md:grid-cols-[300px_1fr] gap-6">
                {/* Product Image */}
                <div className="relative bg-muted">
                  {product.artwork?.image_url ? (
                    <img 
                      src={product.artwork.image_url}
                      alt={product.title}
                      className="w-full h-[300px] object-cover"
                    />
                  ) : (
                    <div className="w-full h-[300px] flex items-center justify-center">
                      <ImageIcon className="h-16 w-16 text-muted-foreground" />
                    </div>
                  )}
                  <Badge className="absolute top-2 left-2">
                    {product.artwork?.style || 'No Style'}
                  </Badge>
                  {product.artwork?.quality_score && (
                    <Badge className="absolute top-2 right-2" variant="secondary">
                      Score: {product.artwork.quality_score}/100
                    </Badge>
                  )}
                </div>

                {/* Product Details */}
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {/* Title */}
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-1 block flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Title
                      </label>
                      <h3 className="text-xl font-bold">{product.title}</h3>
                    </div>

                    {/* Description */}
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-1 block flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Description
                      </label>
                      <p className="text-sm bg-muted p-3 rounded-lg max-h-32 overflow-y-auto">
                        {product.description || 'No description'}
                      </p>
                    </div>

                    {/* Metadata */}
                    <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                      <div>
                        <p className="text-xs text-muted-foreground">SKU</p>
                        <p className="font-mono text-sm">{product.sku}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Price</p>
                        <p className="font-semibold text-sm">£{(product.base_price || 1).toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Status</p>
                        <Badge variant="secondary">{product.status}</Badge>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-4">
                      <Button
                        onClick={() => uploadToShopify(product.id)}
                        disabled={uploading === product.id}
                        className="flex-1"
                      >
                        {uploading === product.id ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                            Uploading...
                          </>
                        ) : (
                          <>
                            <Upload className="h-4 w-4 mr-2" />
                            Upload to Shopify
                          </>
                        )}
                      </Button>
                      <Button variant="outline" size="icon">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="icon">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
