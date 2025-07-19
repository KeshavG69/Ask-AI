
import { useEffect } from "react";

const Index = () => {
  useEffect(() => {
    // Redirect to the widget integration example
    window.location.href = "/widget-integration-example.html";
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">AI Chat Widget</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Redirecting to widget demonstration...
        </p>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
      </div>
    </div>
  );
};

export default Index;
