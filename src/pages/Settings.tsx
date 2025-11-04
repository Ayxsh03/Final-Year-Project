import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

const Settings = () => {
  const { toast } = useToast();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);
  const [settings, setSettings] = useState({
    enabled: true,
    notify_email: false,
    notify_whatsapp: false,
    notify_telegram: false,
    allowed_days: ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
    start_time: "09:30",
    end_time: "18:30",
    timezone: "UTC",
    smtp_host: "",
    smtp_port: "465",
    smtp_username: "",
    smtp_password: "",
    smtp_from: "",
    email_to: "",
    whatsapp_phone_number_id: "",
    whatsapp_token: "",
    whatsapp_to: "",
    telegram_bot_token: "",
    telegram_chat_id: "",
    daily_report_enabled: false,
    weekly_report_enabled: false,
    monthly_report_enabled: false,
    notify_vip_email: false,
    notify_regular_email: false,
    notify_attendance_to_branch: false,
    google_places_api_key: ""
  });

  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/v1/alert-settings');
        if (response.ok) {
          const data = await response.json();
          setSettings({
            enabled: data.enabled ?? true,
            notify_email: data.notify_email ?? false,
            notify_whatsapp: data.notify_whatsapp ?? false,
            notify_telegram: data.notify_telegram ?? false,
            allowed_days: data.allowed_days ?? ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            start_time: data.start_time || "09:30",
            end_time: data.end_time || "18:30",
            timezone: data.timezone || "UTC",
            smtp_host: data.smtp_host ?? "",
            smtp_port: String(data.smtp_port ?? "465"),
            smtp_username: data.smtp_username ?? "",
            smtp_password: data.smtp_password ?? "",
            smtp_from: data.smtp_from ?? "",
            email_to: data.email_to ?? "",
            whatsapp_phone_number_id: data.whatsapp_phone_number_id ?? "",
            whatsapp_token: data.whatsapp_token ?? "",
            whatsapp_to: data.whatsapp_to ?? "",
            telegram_bot_token: data.telegram_bot_token ?? "",
            telegram_chat_id: data.telegram_chat_id ?? "",
            daily_report_enabled: data.daily_report_enabled ?? false,
            weekly_report_enabled: data.weekly_report_enabled ?? false,
            monthly_report_enabled: data.monthly_report_enabled ?? false,
            notify_vip_email: data.notify_vip_email ?? false,
            notify_regular_email: data.notify_regular_email ?? false,
            notify_attendance_to_branch: data.notify_attendance_to_branch ?? false,
            google_places_api_key: data.google_places_api_key ?? ""
          });
        } else {
          toast({
            title: "Error",
            description: "Failed to load settings",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error('Error loading settings:', error);
        toast({
          title: "Error",
          description: "Failed to load settings",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };
    
    loadSettings();
  }, [toast]);

  const saveSettings = async () => {
    setSaving(true);
    try {
      const payload = {
        enabled: settings.enabled,
        notify_email: settings.notify_email,
        notify_whatsapp: settings.notify_whatsapp,
        notify_telegram: settings.notify_telegram,
        allowed_days: settings.allowed_days,
        start_time: settings.start_time || null,
        end_time: settings.end_time || null,
        timezone: settings.timezone || 'UTC',
        smtp_host: settings.smtp_host || null,
        smtp_port: settings.smtp_port ? parseInt(settings.smtp_port as any, 10) : null,
        smtp_username: settings.smtp_username || null,
        smtp_password: settings.smtp_password || null,
        smtp_from: settings.smtp_from || null,
        email_to: settings.email_to || null,
        whatsapp_phone_number_id: settings.whatsapp_phone_number_id || null,
        whatsapp_token: settings.whatsapp_token || null,
        whatsapp_to: settings.whatsapp_to || null,
        telegram_bot_token: settings.telegram_bot_token || null,
        telegram_chat_id: settings.telegram_chat_id || null,
        daily_report_enabled: settings.daily_report_enabled,
        weekly_report_enabled: settings.weekly_report_enabled,
        monthly_report_enabled: settings.monthly_report_enabled,
        notify_vip_email: settings.notify_vip_email,
        notify_regular_email: settings.notify_regular_email,
        notify_attendance_to_branch: settings.notify_attendance_to_branch,
        google_places_api_key: settings.google_places_api_key || null
      };

      const response = await fetch('/api/v1/alert-settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const updatedData = await response.json();
        toast({
          title: "Success",
          description: "Settings saved successfully",
        });
        // Update local state with server response
        setSettings(prev => ({ ...prev, ...updatedData }));
      } else {
        const error = await response.text();
        throw new Error(error);
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      toast({
        title: "Error",
        description: "Failed to save settings",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const testConfiguration = async (alertType: string) => {
    setTesting(alertType);
    try {
      let testSettings = {};
      
      if (alertType === 'email') {
        testSettings = {
          smtp_host: settings.smtp_host,
          smtp_port: settings.smtp_port,
          smtp_username: settings.smtp_username,
          smtp_password: settings.smtp_password,
          smtp_from: settings.smtp_from,
          email_to: settings.email_to
        };
      } else if (alertType === 'whatsapp') {
        testSettings = {
          whatsapp_phone_number_id: settings.whatsapp_phone_number_id,
          whatsapp_token: settings.whatsapp_token,
          whatsapp_to: settings.whatsapp_to
        };
      } else if (alertType === 'telegram') {
        testSettings = {
          telegram_bot_token: settings.telegram_bot_token,
          telegram_chat_id: settings.telegram_chat_id
        };
      }

      const response = await fetch('/api/v1/alert-settings/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          alert_type: alertType,
          settings: testSettings
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        toast({
          title: "Test Successful",
          description: result.message || `${alertType} configuration is working`,
        });
      } else {
        toast({
          title: "Test Failed",
          description: result.error || `${alertType} test failed`,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error testing configuration:', error);
      toast({
        title: "Test Error",
        description: `Failed to test ${alertType} configuration`,
        variant: "destructive",
      });
    } finally {
      setTesting(null);
    }
  };

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  const toggleDay = (day: string) => {
    setSelectedDays(prev => 
      prev.includes(day) 
        ? prev.filter(d => d !== day)
        : [...prev, day]
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
      </div>

      <Card className="bg-card border-border">
        <CardContent className="p-6">
          <Tabs defaultValue="general" className="w-full">
            <TabsList className="grid w-full grid-cols-5 mb-6">
              <TabsTrigger value="general" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                GENERAL
              </TabsTrigger>
              <TabsTrigger value="smtp" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                SMTP
              </TabsTrigger>
              <TabsTrigger value="notification" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                NOTIFICATION
              </TabsTrigger>
              <TabsTrigger value="whatsapp" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                WHATSAPP
              </TabsTrigger>
              <TabsTrigger value="telegram" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                TELEGRAM
              </TabsTrigger>
            </TabsList>

            <TabsContent value="general" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="google-api" className="text-foreground">
                    Google place API <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="google-api"
                    placeholder="AIzaSyDk-"
                    value={settings.google_places_api_key}
                    onChange={(e) => setSettings((s) => ({ ...s, google_places_api_key: e.target.value }))}
                    className="bg-background border-primary"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-foreground">
                    Allowed days
                  </Label>
                  <div className="flex flex-wrap gap-2">
                    {days.map((day) => (
                      <Badge
                        key={day}
                        variant={settings.allowed_days.includes(day) ? "default" : "outline"}
                        className={`cursor-pointer ${
                          settings.allowed_days.includes(day)
                            ? "bg-primary text-primary-foreground"
                            : "border-muted-foreground hover:bg-muted"
                        }`}
                        onClick={() => setSettings((s) => ({
                          ...s,
                          allowed_days: s.allowed_days.includes(day)
                            ? s.allowed_days.filter((d: string) => d !== day)
                            : [...s.allowed_days, day]
                        }))}
                      >
                        {day}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="start-time" className="text-foreground">
                    Office Start Time <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="start-time"
                    type="time"
                    value={settings.start_time}
                    onChange={(e) => setSettings((s) => ({ ...s, start_time: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end-time" className="text-foreground">
                    Office End Time <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="end-time"
                    type="time"
                    value={settings.end_time}
                    onChange={(e) => setSettings((s) => ({ ...s, end_time: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timezone" className="text-foreground">Timezone</Label>
                  <Input
                    id="timezone"
                    placeholder="UTC or Continent/City"
                    value={settings.timezone}
                    onChange={(e) => setSettings((s) => ({ ...s, timezone: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground">Notification</h3>
                <div className="flex items-center justify-between">
                  <span className="text-foreground">Enable alerts</span>
                  <Switch
                    checked={settings.enabled}
                    onCheckedChange={(v) => setSettings((s) => ({ ...s, enabled: !!v }))}
                    className="data-[state=checked]:bg-primary"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button variant="outline">Cancel</Button>
                <Button className="bg-primary hover:bg-primary/90 text-primary-foreground" onClick={saveSettings} disabled={saving}>
                  {saving ? "Saving..." : "Save Settings"}
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="smtp" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="from-mail" className="text-foreground">
                    From mail ID <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="from-mail"
                    placeholder="alerts@example.com"
                    value={settings.smtp_from}
                    onChange={(e) => setSettings((s) => ({ ...s, smtp_from: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="host" className="text-foreground">
                    Host <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="host"
                    placeholder="smtp.zoho.in"
                    value={settings.smtp_host}
                    onChange={(e) => setSettings((s) => ({ ...s, smtp_host: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username" className="text-foreground">
                    Username <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="username"
                    placeholder="smtp username"
                    value={settings.smtp_username}
                    onChange={(e) => setSettings((s) => ({ ...s, smtp_username: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-foreground">
                    Password <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    value={settings.smtp_password}
                    onChange={(e) => setSettings((s) => ({ ...s, smtp_password: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="port" className="text-foreground">
                    Port <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="port"
                    placeholder="465"
                    value={settings.smtp_port}
                    onChange={(e) => setSettings((s) => ({ ...s, smtp_port: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email-to" className="text-foreground">
                    Send alerts to (comma-separated emails)
                  </Label>
                  <Input
                    id="email-to"
                    placeholder="ops@example.com"
                    value={settings.email_to}
                    onChange={(e) => setSettings((s) => ({ ...s, email_to: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>
              </div>

              <div className="flex justify-between items-center">
                <Button 
                  variant="outline" 
                  onClick={() => testConfiguration('email')}
                  disabled={testing === 'email' || !settings.smtp_host || !settings.smtp_username}
                  className="flex items-center gap-2"
                >
                  {testing === 'email' ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                      Testing...
                    </>
                  ) : (
                    <>🧪 Test Email</>
                  )}
                </Button>
                <div className="flex gap-3">
                  <Button variant="outline">Cancel</Button>
                  <Button className="bg-primary hover:bg-primary/90 text-primary-foreground" onClick={saveSettings} disabled={saving}>
                    {saving ? "Saving..." : "Save Settings"}
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="notification" className="space-y-6">
              <div className="space-y-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-foreground">Notification Settings</h3>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-foreground">Email alerts</span>
                    <Switch
                      checked={settings.notify_email}
                      onCheckedChange={(v) => setSettings((s) => ({ ...s, notify_email: !!v }))}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-foreground">2. Need to notify attendance to branch contact</span>
                    <Switch
                      defaultChecked={true}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-md font-semibold text-foreground">3. Notification Reports Email</h4>
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-foreground">Daily Events Report</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">No</span>
                          <Switch
                            checked={settings.daily_report_enabled}
                            onCheckedChange={(v) => setSettings((s) => ({ ...s, daily_report_enabled: !!v }))}
                            className="data-[state=checked]:bg-primary"
                          />
                          <span className="text-sm text-muted-foreground">Yes</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-foreground">Weekly Events Report</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">No</span>
                          <Switch
                            checked={settings.weekly_report_enabled}
                            onCheckedChange={(v) => setSettings((s) => ({ ...s, weekly_report_enabled: !!v }))}
                            className="data-[state=checked]:bg-primary"
                          />
                          <span className="text-sm text-muted-foreground">Yes</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-foreground">Monthly Events Report</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">No</span>
                          <Switch
                            checked={settings.monthly_report_enabled}
                            onCheckedChange={(v) => setSettings((s) => ({ ...s, monthly_report_enabled: !!v }))}
                            className="data-[state=checked]:bg-primary"
                          />
                          <span className="text-sm text-muted-foreground">Yes</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-md font-semibold text-foreground">4. Notify about the customer arrival</h4>
                    
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h5 className="text-center text-foreground mb-4">VIP</h5>
                        <div className="space-y-3">
                          <div className="space-y-2">
                            <Label className="text-foreground">Email</Label>
                            <div className="flex items-center space-x-2">
                              <Checkbox 
                                id="vip-email"
                                className="border-border data-[state=checked]:bg-primary"
                              />
                              <Label htmlFor="vip-email" className="text-sm text-foreground">
                                Current branch manager + Admin
                              </Label>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h5 className="text-center text-foreground mb-4">Regular</h5>
                        <div className="space-y-3">
                          <div className="space-y-2">
                            <Label className="text-foreground">Email</Label>
                            <div className="flex items-center space-x-2">
                              <Checkbox 
                                id="regular-email"
                                className="border-border data-[state=checked]:bg-primary"
                              />
                              <Label htmlFor="regular-email" className="text-sm text-foreground">
                                Current branch manager + Admin
                              </Label>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-md font-semibold text-foreground">Blocked</h4>
                    {/* Add blocked notifications content here */}
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end gap-3">
                <Button variant="outline">Cancel</Button>
                <Button className="bg-primary hover:bg-primary/90 text-primary-foreground" onClick={saveSettings} disabled={saving}>
                  {saving ? "Saving..." : "Save Settings"}
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="whatsapp" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="whatsapp-id" className="text-foreground">
                    Whatsapp Id <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="whatsapp-id"
                    placeholder="194780447058170"
                    value={settings.whatsapp_phone_number_id}
                    onChange={(e) => setSettings((s) => ({ ...s, whatsapp_phone_number_id: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="whatsapp-token" className="text-foreground">
                    Whatsapp token <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="whatsapp-token"
                    placeholder="EAAX..."
                    value={settings.whatsapp_token}
                    onChange={(e) => setSettings((s) => ({ ...s, whatsapp_token: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="whatsapp-to" className="text-foreground">
                    WhatsApp To (E.164)
                  </Label>
                  <Input
                    id="whatsapp-to"
                    placeholder="+15551234567"
                    value={settings.whatsapp_to}
                    onChange={(e) => setSettings((s) => ({ ...s, whatsapp_to: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-foreground">WhatsApp alerts</span>
                  <Switch
                    checked={settings.notify_whatsapp}
                    onCheckedChange={(v) => setSettings((s) => ({ ...s, notify_whatsapp: !!v }))}
                    className="data-[state=checked]:bg-primary"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-foreground">
                    Event Types <span className="text-red-500">*</span>
                  </Label>
                  <Select defaultValue="footfall">
                    <SelectTrigger className="bg-background border-border">
                      <SelectValue placeholder="Select the event types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="footfall">
                        <Badge variant="secondary" className="bg-primary/10 text-primary mr-2">
                          Footfall
                        </Badge>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <Button 
                  variant="outline" 
                  onClick={() => testConfiguration('whatsapp')}
                  disabled={testing === 'whatsapp' || !settings.whatsapp_phone_number_id || !settings.whatsapp_token}
                  className="flex items-center gap-2"
                >
                  {testing === 'whatsapp' ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                      Testing...
                    </>
                  ) : (
                    <>🧪 Test WhatsApp</>
                  )}
                </Button>
                <div className="flex gap-3">
                  <Button variant="outline">Cancel</Button>
                  <Button className="bg-primary hover:bg-primary/90 text-primary-foreground" onClick={saveSettings} disabled={saving}>
                    {saving ? "Saving..." : "Save Settings"}
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="telegram" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="telegram-id" className="text-foreground">
                    Telegram Id <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="telegram-id"
                    placeholder="Chat ID"
                    value={settings.telegram_chat_id}
                    onChange={(e) => setSettings((s) => ({ ...s, telegram_chat_id: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="telegram-token" className="text-foreground">
                    Telegram token <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="telegram-token"
                    placeholder="123456:AA..."
                    value={settings.telegram_bot_token}
                    onChange={(e) => setSettings((s) => ({ ...s, telegram_bot_token: e.target.value }))}
                    className="bg-background border-border"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-foreground">Telegram alerts</span>
                  <Switch
                    checked={settings.notify_telegram}
                    onCheckedChange={(v) => setSettings((s) => ({ ...s, notify_telegram: !!v }))}
                    className="data-[state=checked]:bg-primary"
                  />
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <Button 
                  variant="outline" 
                  onClick={() => testConfiguration('telegram')}
                  disabled={testing === 'telegram' || !settings.telegram_bot_token || !settings.telegram_chat_id}
                  className="flex items-center gap-2"
                >
                  {testing === 'telegram' ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                      Testing...
                    </>
                  ) : (
                    <>🧪 Test Telegram</>
                  )}
                </Button>
                <div className="flex gap-3">
                  <Button variant="outline">Cancel</Button>
                  <Button className="bg-primary hover:bg-primary/90 text-primary-foreground" onClick={saveSettings} disabled={saving}>
                    {saving ? "Saving..." : "Save Settings"}
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;