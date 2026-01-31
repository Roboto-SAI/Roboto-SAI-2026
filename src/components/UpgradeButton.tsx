import { Button } from "@/components/ui/button";
import { loadStripe } from "@stripe/stripe-js";
import { Zap } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/authStore";

// Initialize Stripe outside component to avoid recreation
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || "");

export const UpgradeButton = () => {
    const [loading, setLoading] = useState(false);
    const { user } = useAuthStore();

    // Don't show if already premium
    if (user?.subscription_status === 'active') {
        return null;
    }

    const handleUpgrade = async () => {
        setLoading(true);
        try {
            const stripe = await stripePromise;
            if (!stripe) throw new Error("Stripe failed to load");

            // Call backend to create session
            const response = await fetch(`${import.meta.env.VITE_API_URL || ""}/api/create-checkout-session`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    success_url: window.location.origin + "/chat?success=true",
                    cancel_url: window.location.origin + "/chat?canceled=true",
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Failed to start checkout");
            }

            const { sessionId } = await response.json();

            // Redirect to checkout
            const result = await stripe.redirectToCheckout({
                sessionId,
            });

            if (result.error) {
                throw new Error(result.error.message);
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
