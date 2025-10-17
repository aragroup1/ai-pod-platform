"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle } from 'lucide-react';
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

// --- Main Dashboard Component ---
export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentProducts, setRecentProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // This will be automatically set by Railway's environment variables
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

    useEffect(() => {
    const fetchData = async () => {
      // This is now the main guard
      if (!API_URL) {
          setError("API URL environment variable (NEXT_PUBLIC_API_URL) is not configured.");
          setLoading(false);
          return;
      }

      try {
        setLoading(true);
        setError(null);

        // ... rest of the fetch logic remains the same
        const [statsResponse, productsResponse] = await Promise.all([
          fetch(`${API_URL}/api/v1/analytics/dashboard`),
          fetch(`${API_URL}/api/v1/products?limit=5`)
        ]);

        if (!statsResponse.ok) throw new Error(`Dashboard stats fetch failed (Status: ${statsResponse.status})`);
        if (!productsResponse.ok) throw new Error(`Recent products fetch failed (Status: ${productsResponse.status})`);
        // ... rest of the logic
        const statsData = await statsResponse.json();
        const productsData = await productsResponse.json();

        // Use a mix of real and placeholder data
        setStats({
          revenue: statsData.revenue || 12540.50,
          orders: statsData.orders || 431,
          products: productsData.products.length || 78,
          trends: 15,
        });
        setRecentProducts(productsData.products || []);

        toast.success("Dashboard data loaded successfully!");

      } catch (err: any) {
        setError(err.message);
        toast.error(`Error: ${err.message}`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [API_URL]);

  if (error) {
    return (
        <div className="flex items-center justify-center h-screen bg-background text-destructive">
            <div className="text-center p-8">
                <AlertCircle className="mx-auto h-12 w-12" />
                <h2 className="mt-4 text-2xl font-bold">Failed to Connect to API</h2>
                <p className="mt-2 text-muted-foreground break-all">
                    Could not fetch data from: <code className="bg-muted px-2 py-1 rounded-md">{API_URL}</code>
                </p>
                <p className="mt-2 text-sm text-muted-foreground">
                    <b>Details:</b> {error}
                </p>
                <p className="mt-4 text-sm text-muted-foreground">
                    Please check your backend deployment logs on Railway and ensure the `NEXT_PUBLIC_API_URL` environment variable is set correctly for this frontend service.
                </p>
                <Button onClick={() => window.location.reload()} className="mt-6">Retry Connection</Button>
            </div>
        </div>
    );
  }

  const chartData = [
    { name: 'Mon', revenue: 4000 }, { name: 'Tue', revenue: 3000 },
    { name: 'Wed', revenue: 2000 }, { name: 'Thu', revenue: 2780 },
    { name: 'Fri', revenue: 1890 }, { name: 'Sat', revenue: 2390 },
    { name: 'Sun', revenue: 3490 },
  ];

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-muted/40">
      <Toaster richColors />
      <div className="w-full max-w-7xl space-y-6">
        <header className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">AI POD Dashboard</h1>
          <Button>Generate New Products</Button>
        </header>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">£{stats?.revenue.toLocaleString() || '...'}</div>
              <p className="text-xs text-muted-foreground">+20.1% from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Orders</CardTitle>
              <ShoppingCart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">+{stats?.orders.toLocaleString() || '...'}</div>
              <p className="text-xs text-muted-foreground">+180.1% from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Products</CardTitle>
              <Palette className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.products.toLocaleString() || '...'}</div>
              <p className="text-xs text-muted-foreground">+19 from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Trending Topics</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.trends.toLocaleString() || '...'}</div>
              <p className="text-xs text-muted-foreground">+5 identified this week</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader><CardTitle>Revenue Overview</CardTitle></CardHeader>
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
            <CardHeader><CardTitle>Recent Products</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead><TableHead>Status</TableHead><TableHead>Price</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentProducts.length > 0 ? recentProducts.map(product => (
                    <TableRow key={product.id}>
                      <TableCell className="font-medium">{product.title}</TableCell>
                      <TableCell>
                        <Badge>{product.status}</Badge>
                      </TableCell>
                      <TableCell>£{product.base_price}</TableCell>
                    </TableRow>
                  )) : (
                    <TableRow><TableCell colSpan={3} className="text-center">No recent products.</TableCell></TableRow>
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
