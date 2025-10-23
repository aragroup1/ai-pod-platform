"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, Play, RefreshCw, Zap } from 'lucide-react';
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

// --- Main Dashboard Component ---
export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentProducts, setRecentProducts] = useState<Product[]>([]);
  const [genStatus, setGenStatus] = useState<GenerationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isFetchingTrends, setIsFetchingTrends] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

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

      const [statsResponse, productsResponse, genStatusResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/analytics/dashboard`),
        fetch(`${API_URL}/api/v1/products?limit=5`),
        fetch(`${API_URL}/api/v1/generation/status`)
      ]);

      if (!statsResponse.ok || !productsResponse.ok || !genStatusResponse.ok) {
        throw new Error('Failed to fetch data');
      }

      const statsData = await statsResponse.json();
      const productsData = await productsResponse.json();
      const genStatusData = await genStatusResponse.json();

      setStats({
        revenue: statsData.revenue || 0,
        orders: statsData.orders || 0,
        products: statsData.products || 0,
        trends: statsData.trends || 0,
      });
      
      setRecentProducts(productsData.products || []);
      setGenStatus(genStatusData);

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
        method: 'POST'
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

  // Generate Products
  const generateProducts = async () => {
    if (!API_URL) return;

    setIsGenerating(true);
    toast.info("Starting product generation...");

    try {
      const response = await fetch(`${API_URL}/api/v1/generation/batch-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          limit: 2,
          min_trend_score: 6.0,
          testing_mode: true,
          upscale: false
        })
      });

      if (!response.ok) throw new Error('Generation failed');

      const data = await response.json();
      toast.success(`Generating ${data.expected_products} products!`);
      
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
  }, [API_URL]);

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
            <h1 className="text-3xl font-bold">AI POD Dashboard</h1>
            <p className="text-muted-foreground">Automated Print-on-Demand Platform</p>
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
              onClick={generateProducts}
              disabled={isGenerating || (genStatus?.trends_awaiting_generation || 0) === 0}
            >
              <Zap className={`h-4 w-4 mr-2 ${isGenerating ? 'animate-pulse' : ''}`} />
              Generate Products
            </Button>
          </div>
        </header>

        {/* Generation Status Alert */}
        {genStatus && genStatus.trends_awaiting_generation > 0 && (
          <Card className="border-blue-500 bg-blue-50 dark:bg-blue-950">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold">Ready to Generate!</p>
                  <p className="text-sm text-muted-foreground">
                    {genStatus.trends_awaiting_generation} trends are waiting for product generation
                  </p>
                </div>
                <Button onClick={generateProducts} disabled={isGenerating}>
                  <Play className="h-4 w-4 mr-2" />
                  Generate Now
                </Button>
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
                        No products yet. Click "Generate Products" to create some!
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
