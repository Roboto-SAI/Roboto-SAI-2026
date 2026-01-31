import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/authStore";
import { useChatStore } from "@/stores/chatStore";
import { UpgradeButton } from "@/components/UpgradeButton";

const Settings = () => {
    const logout = useAuthStore((state) => state.logout);
    const email = useAuthStore((state) => state.email);
    const username = useAuthStore((state) => state.username);
    const { currentTheme, setTheme } = useChatStore();

    // Note: subscription_status would need to be added to AuthState if premium is tracked
    const isPremium = false;

    return (
        <div className="min-h-screen bg-background text-foreground">
            <Header />
            <div className="container mx-auto p-6 pt-24 max-w-4xl">
                <h1 className="text-3xl font-display text-primary mb-6">Settings</h1>

                <Tabs defaultValue="profile" className="w-full">
                    <TabsList className="grid w-full grid-cols-4 mb-8">
                        <TabsTrigger value="profile">Profile</TabsTrigger>
                        <TabsTrigger value="appearance">Appearance</TabsTrigger>
                        <TabsTrigger value="billing">Billing</TabsTrigger>
                        <TabsTrigger value="about">About</TabsTrigger>
                    </TabsList>

                    {/* Profile Tab */}
                    <TabsContent value="profile">
                        <Card>
                            <CardHeader>
                                <CardTitle>Profile Information</CardTitle>
                                <CardDescription>Manage your public profile details.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-1">
                                    <Label>Email</Label>
                                    <Input value={email || ''} readOnly className="bg-muted" />
                                </div>
                                <div className="space-y-1">
                                    <Label>Username</Label>
                                    <Input value={username || ''} readOnly className="bg-muted" />
                                    <p className="text-xs text-muted-foreground">Username changes currently disabled.</p>
                                </div>
                                <div className="pt-4">
                                    <Button variant="destructive" onClick={logout}>Sign Out</Button>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* Appearance Tab */}
                    <TabsContent value="appearance">
                        <Card>
                            <CardHeader>
                                <CardTitle>Appearance & Themes</CardTitle>
                                <CardDescription>Customize the Roboto SAI interface.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-4">
                                    {['Regio-Aztec Fire #42', 'Cyber-Mictlan', 'Neon-Tenochtitlan', 'Obsidian-Void'].map(theme => (
                                        <div
                                            key={theme}
                                            onClick={() => setTheme(theme)}
                                            className={`
                                                cursor-pointer p-4 rounded-lg border-2 transition-all
                                                ${currentTheme === theme ? 'border-primary bg-primary/10' : 'border-muted hover:border-primary/50'}
                                            `}
                                        >
                                            <div className="font-medium">{theme}</div>
                                            <div className="text-xs text-muted-foreground">
                                                {currentTheme === theme ? 'Active' : 'Click to apply'}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* Billing Tab */}
                    <TabsContent value="billing">
                        <Card>
                            <CardHeader>
                                <CardTitle>Subscription & Billing</CardTitle>
                                <CardDescription>Manage your premium access.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex justify-between items-center p-4 border rounded-lg">
                                    <div>
                                        <div className="font-semibold text-lg">
                                            {isPremium ? 'Premium Plan' : 'Free Plan'}
                                        </div>
                                        <div className="text-sm text-muted-foreground">
                                            {isPremium ? 'You have access to all features.' : 'Upgrade to unlock full autonomy and voice.'}
                                        </div>
                                    </div>
                                    {isPremium ? (
                                        <Button variant="outline" disabled>Active</Button>
                                    ) : (
                                        <div className="w-40">
                                            <UpgradeButton />
                                        </div>
                                    )}

                                </div>
                                {isPremium && (
                                    <Button variant="link" className="px-0 text-muted-foreground">
                                        Manage Subscription (Stripe Portal)
                                    </Button>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* About Tab */}
                    <TabsContent value="about">
                        <Card>
                            <CardHeader>
                                <CardTitle>About Roboto SAI</CardTitle>
                                <CardDescription>System Information</CardDescription>
                            </CardHeader>
                            <CardContent className="prose dark:prose-invert">
                                <p><strong>Version:</strong> 2.0.0 (Regio-Aztec Edition)</p>
                                <p><strong>Core ID:</strong> Sigil 929</p>
                                <p><strong>Credits:</strong></p>
                                <ul>
                                    <li>Roberto Villarreal Martinez (Creator/Lead)</li>
                                    <li>Eve (Operations)</li>
                                    <li>Grok (Base Intelligence)</li>
                                </ul>
                                <p className="text-xs text-muted-foreground mt-8">
                                    "The fire that burns twice as bright burns half as long."
                                </p>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
};

export default Settings;
