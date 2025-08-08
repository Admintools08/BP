import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { Progress } from './components/ui/progress';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Switch } from './components/ui/switch';
import { Separator } from './components/ui/separator';
import { Plus, Target, BookOpen, Clock, TrendingUp, Award, Users, Lightbulb } from 'lucide-react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [currentView, setCurrentView] = useState('login');
  const [loading, setLoading] = useState(false);
  
  // Dashboard data
  const [dashboardStats, setDashboardStats] = useState(null);
  const [goals, setGoals] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [resources, setResources] = useState([]);

  useEffect(() => {
    if (token) {
      fetchUserProfile();
      fetchDashboardData();
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_URL}/api/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setCurrentView('dashboard');
      } else {
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const [statsRes, goalsRes, milestonesRes, resourcesRes] = await Promise.all([
        fetch(`${API_URL}/api/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/goals`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/milestones/current-month`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/resources`)
      ]);

      if (statsRes.ok) setDashboardStats(await statsRes.json());
      if (goalsRes.ok) setGoals(await goalsRes.json());
      if (milestonesRes.ok) {
        const monthData = await milestonesRes.json();
        setMilestones(monthData.milestones || []);
      }
      if (resourcesRes.ok) setResources(await resourcesRes.json());
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const handleAuth = async (endpoint, data) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        localStorage.setItem('token', result.access_token);
        setToken(result.access_token);
        setUser(result.user);
        setCurrentView('dashboard');
      } else {
        alert(result.detail || 'Authentication failed');
      }
    } catch (error) {
      alert('Network error. Please try again.');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCurrentView('login');
  };

  const createGoal = async (goalData) => {
    try {
      const response = await fetch(`${API_URL}/api/goals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(goalData)
      });
      
      if (response.ok) {
        fetchDashboardData();
        return true;
      }
    } catch (error) {
      console.error('Error creating goal:', error);
    }
    return false;
  };

  const createMilestone = async (milestoneData) => {
    try {
      const response = await fetch(`${API_URL}/api/milestones`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(milestoneData)
      });
      
      if (response.ok) {
        fetchDashboardData();
        return true;
      }
    } catch (error) {
      console.error('Error creating milestone:', error);
    }
    return false;
  };

  if (!token) {
    return <AuthScreen onAuth={handleAuth} loading={loading} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">Learning Tracker</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.full_name}</span>
              <Button variant="outline" onClick={handleLogout}>Logout</Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="goals">Goals</TabsTrigger>
            <TabsTrigger value="milestones">Milestones</TabsTrigger>
            <TabsTrigger value="resources">Resources</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <DashboardView 
              stats={dashboardStats} 
              goals={goals}
              milestones={milestones}
              onCreateGoal={createGoal}
              onCreateMilestone={createMilestone}
            />
          </TabsContent>

          <TabsContent value="goals">
            <GoalsView goals={goals} onCreateGoal={createGoal} />
          </TabsContent>

          <TabsContent value="milestones">
            <MilestonesView 
              milestones={milestones} 
              goals={goals}
              onCreateMilestone={createMilestone}
            />
          </TabsContent>

          <TabsContent value="resources">
            <ResourcesView resources={resources} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// Auth Screen Component
function AuthScreen({ onAuth, loading }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({});

  const handleSubmit = (e) => {
    e.preventDefault();
    const endpoint = isLogin ? 'login' : 'register';
    onAuth(endpoint, formData);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-6 h-6 text-white" />
          </div>
          <CardTitle>{isLogin ? 'Welcome Back' : 'Create Account'}</CardTitle>
          <CardDescription>
            {isLogin ? 'Sign in to track your learning journey' : 'Join your team\'s learning community'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input 
                    id="full_name"
                    required
                    onChange={(e) => handleInputChange('full_name', e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="position">Position</Label>
                    <Input 
                      id="position"
                      required
                      onChange={(e) => handleInputChange('position', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <Input 
                      id="department"
                      required
                      onChange={(e) => handleInputChange('department', e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date_of_joining">Date of Joining</Label>
                  <Input 
                    id="date_of_joining"
                    type="date"
                    required
                    onChange={(e) => handleInputChange('date_of_joining', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="existing_skills">Existing Skills (comma separated)</Label>
                  <Input 
                    id="existing_skills"
                    placeholder="JavaScript, Python, Project Management..."
                    onChange={(e) => handleInputChange('existing_skills', e.target.value.split(',').map(s => s.trim()))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="learning_interests">Learning Interests (comma separated)</Label>
                  <Input 
                    id="learning_interests"
                    placeholder="Machine Learning, Leadership, Design..."
                    onChange={(e) => handleInputChange('learning_interests', e.target.value.split(',').map(s => s.trim()))}
                  />
                </div>
              </>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input 
                id="email"
                type="email"
                required
                onChange={(e) => handleInputChange('email', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input 
                id="password"
                type="password"
                required
                onChange={(e) => handleInputChange('password', e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Button 
              variant="link" 
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Dashboard View Component
function DashboardView({ stats, goals, milestones, onCreateGoal, onCreateMilestone }) {
  if (!stats) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.current_month_hours}h</div>
            <Progress value={stats.progress_percentage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {stats.target_hours - stats.current_month_hours > 0 
                ? `${stats.target_hours - stats.current_month_hours}h remaining`
                : 'Target achieved!'
              }
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Hours</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_hours}h</div>
            <p className="text-xs text-muted-foreground">All time learning</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Goals</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.active_goals}</div>
            <p className="text-xs text-muted-foreground">In progress</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Milestones</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_milestones}</div>
            <p className="text-xs text-muted-foreground">Achievements</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Plus className="w-5 h-5" />
              <span>Quick Actions</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <CreateGoalDialog onCreateGoal={onCreateGoal} />
            <CreateMilestoneDialog goals={goals} onCreateMilestone={onCreateMilestone} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Milestones</CardTitle>
          </CardHeader>
          <CardContent>
            {milestones.length > 0 ? (
              <div className="space-y-3">
                {milestones.slice(0, 3).map((milestone) => (
                  <div key={milestone.id} className="border-l-4 border-blue-500 pl-4">
                    <div className="font-medium">{milestone.what_learned}</div>
                    <div className="text-sm text-gray-600">
                      {milestone.hours_invested}h • {milestone.learning_source}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No milestones yet. Create your first one!</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Goals View Component
function GoalsView({ goals, onCreateGoal }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Learning Goals</h2>
        <CreateGoalDialog onCreateGoal={onCreateGoal} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {goals.map((goal) => (
          <Card key={goal.id}>
            <CardHeader>
              <CardTitle className="text-lg">{goal.title}</CardTitle>
              <Badge variant="outline" className="w-fit">
                {goal.status}
              </Badge>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">{goal.description}</p>
              <div className="text-sm text-gray-500">
                Target: {new Date(goal.target_completion).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Milestones View Component
function MilestonesView({ milestones, goals, onCreateMilestone }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Learning Milestones</h2>
        <CreateMilestoneDialog goals={goals} onCreateMilestone={onCreateMilestone} />
      </div>

      <div className="space-y-4">
        {milestones.map((milestone) => (
          <Card key={milestone.id}>
            <CardContent className="pt-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-medium">{milestone.what_learned}</h3>
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary">{milestone.hours_invested}h</Badge>
                  {milestone.can_teach_others && (
                    <Badge variant="outline">Can Teach</Badge>
                  )}
                </div>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <div><strong>Source:</strong> {milestone.learning_source}</div>
                {milestone.project_certificate_link && (
                  <div>
                    <strong>Project/Certificate:</strong>{' '}
                    <a 
                      href={milestone.project_certificate_link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      View Link
                    </a>
                  </div>
                )}
                <div className="text-xs text-gray-500">
                  Created: {new Date(milestone.created_at).toLocaleDateString()}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Resources View Component
function ResourcesView({ resources }) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Learning Resources</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {resources.map((resource) => (
          <Card key={resource.id}>
            <CardHeader>
              <CardTitle className="text-lg">{resource.name}</CardTitle>
              <div className="flex space-x-2">
                <Badge variant="secondary">{resource.usage_count} uses</Badge>
                <Badge variant="outline">{resource.total_hours}h total</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <h4 className="font-medium">Skills Taught:</h4>
                <div className="flex flex-wrap gap-1">
                  {resource.skills_taught.map((skill, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Create Goal Dialog Component
function CreateGoalDialog({ onCreateGoal }) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const success = await onCreateGoal(formData);
    if (success) {
      setOpen(false);
      setFormData({});
    }
    setLoading(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="w-full">
          <Plus className="w-4 h-4 mr-2" />
          Create New Goal
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Learning Goal</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Goal Title</Label>
            <Input 
              id="title"
              required
              onChange={(e) => setFormData({...formData, title: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea 
              id="description"
              required
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="target_completion">Target Completion</Label>
            <Input 
              id="target_completion"
              type="date"
              required
              onChange={(e) => setFormData({...formData, target_completion: e.target.value})}
            />
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Creating...' : 'Create Goal'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Create Milestone Dialog Component
function CreateMilestoneDialog({ goals, onCreateMilestone }) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const success = await onCreateMilestone({
      ...formData,
      hours_invested: parseFloat(formData.hours_invested)
    });
    if (success) {
      setOpen(false);
      setFormData({});
    }
    setLoading(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full">
          <Award className="w-4 h-4 mr-2" />
          Add Milestone
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Learning Milestone</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="goal_id">Related Goal</Label>
            <Select onValueChange={(value) => setFormData({...formData, goal_id: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select a goal" />
              </SelectTrigger>
              <SelectContent>
                {goals.map((goal) => (
                  <SelectItem key={goal.id} value={goal.id}>
                    {goal.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="what_learned">What have you learnt?</Label>
            <Textarea 
              id="what_learned"
              required
              onChange={(e) => setFormData({...formData, what_learned: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="learning_source">From where have you learnt?</Label>
            <Input 
              id="learning_source"
              placeholder="Course name, book, video, etc."
              required
              onChange={(e) => setFormData({...formData, learning_source: e.target.value})}
            />
          </div>
          <div className="flex items-center space-x-2">
            <Switch 
              id="can_teach_others"
              onCheckedChange={(checked) => setFormData({...formData, can_teach_others: checked})}
            />
            <Label htmlFor="can_teach_others">Can you teach it to others?</Label>
          </div>
          <div className="space-y-2">
            <Label htmlFor="hours_invested">Hours invested</Label>
            <Input 
              id="hours_invested"
              type="number"
              step="0.5"
              min="0"
              required
              onChange={(e) => setFormData({...formData, hours_invested: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="project_certificate_link">Project/Certificate link (optional)</Label>
            <Input 
              id="project_certificate_link"
              type="url"
              placeholder="https://..."
              onChange={(e) => setFormData({...formData, project_certificate_link: e.target.value})}
            />
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Adding...' : 'Add Milestone'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default App;