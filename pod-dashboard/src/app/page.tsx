// Alternative: Show BOTH boxes side-by-side
// Replace lines 451-554 in your dashboard with this:

        {/* Keyword & Launch Section - Always visible */}
        {!showGallery && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
