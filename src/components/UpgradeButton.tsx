import { Button } from "@/components/ui/button";
import { Zap } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/authStore";

export const UpgradeButton = () => {
    const [loading, setLoading] = useState(false);
    const isLoggedIn = useAuthStore((state) => state.isLoggedIn);

    const handleUpgrade = async () => {
        if (!isLoggedIn) {
            toast.error("Please log in to upgrade");
            return;
        }

        setLoading(true);
        try {
            // Call backend to create session - backend returns the checkout URL
            const response = await fetch(`${import.meta.env.VITE_API_URL || ""}/api/create-checkout-session`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify({
                    success_url: window.location.origin + "/chat?success=true",
                    cancel_url: window.location.origin + "/chat?canceled=true",
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Failed to start checkout");
            }

            const data = await response.json();
            
            // Stripe Checkout Sessions return a url property for redirect
            if (data.url) {
                window.location.href = data.url;
            } else if (data.sessionId) {
                // Fallback: construct Stripe checkout URL from session ID
                window.location.href = `https://checkout.stripe.com/c/pay/${data.sessionId}`;
            } else {
                throw new Error("No checkout URL returned");
            }

        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : "Unknown error";
            console.error("Upgrade error:", error);
            toast.error("Failed to start upgrade: " + message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Button
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-white border-0 shadow-lg shadow-amber-500/20"
        >
            <Zap className="w-4 h-4 mr-2 fill-current" />
            {loading ? "Loading..." : "Upgrade to Premium"}
        </Button>
    );
};