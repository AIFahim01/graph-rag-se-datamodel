# Interactive Graph Guide - How to See Project Relationships

## 🎯 Quick Answer

**YES! Project-to-project relationships ARE in the graph!**

They are the **PINK/MAGENTA BOLD LINES** connecting the large project boxes!

## 📁 Open This File

```
C:\Users\User\PycharmProjects\pdf-to-graphrag\datasets\knowledge_graphs\project_relationships_interactive.html
```

## 👀 What to Look For

### Project Nodes (Large Boxes)
```
┌─────────────────────────────┐
│   Alpha ERP System          │ ← RED BOX (large)
└─────────────────────────────┘

┌─────────────────────────────┐
│   Beta Cloud Migration      │ ← TEAL BOX (large)
└─────────────────────────────┘

┌─────────────────────────────┐
│ Gamma Analytics Platform    │ ← MINT BOX (large)
└─────────────────────────────┘
```

### Project-to-Project Lines (PINK - Look for These!)
```
      Alpha ERP
          │
    PINK LINE labeled "DATABASE"
          │
          ↓
    Beta Cloud Migration
          │
    PINK LINE labeled "CLOUD"
          │
          ↓
  Gamma Analytics Platform
```

## 🔍 8 Project Relationships Created

### 1. Alpha ↔ Beta (3 connections)
- **PINK LINE labeled "ANALYTICS"** - Both use analytics tech
- **PINK LINE labeled "DATABASE"** - Both use database tech
- **PINK LINE labeled "SIMILAR"** - Similar tech stacks

### 2. Alpha ↔ Gamma (1 connection)
- **PINK LINE labeled "ANALYTICS"** - Both use analytics tech

### 3. Beta ↔ Gamma (4 connections) - STRONGEST!
- **PINK LINE labeled "INTEGRATION"** - Both use integration tech
- **PINK LINE labeled "ANALYTICS"** - Both use analytics tech
- **PINK LINE labeled "CLOUD"** - Both use cloud tech
- **PINK LINE labeled "SIMILAR"** - Very similar tech stacks

## 🎨 Visual Legend

### Colors in the Graph:

| Color | Meaning |
|-------|---------|
| 🟥 Red box | Alpha ERP System (project) |
| 🟦 Teal box | Beta Cloud Migration (project) |
| 🟩 Mint box | Gamma Analytics Platform (project) |
| 🟣 **PINK/Magenta lines** | **Project-to-Project relationships** ⭐ |
| ⚪ Gray dashed lines | Project-to-Entity connections |
| 🔴🔵🟢 Colored circles | Top entities from each project |

## 🖱️ How to Explore

### Step 1: Open the HTML file in browser

### Step 2: Look for the 3 large colored boxes
- These are your projects
- They should be prominent and easy to spot

### Step 3: Look for PINK/MAGENTA lines between boxes
- These show how projects relate
- Hover over them to see details

### Step 4: Interact
- **Drag** project boxes apart to see connections clearly
- **Hover** over pink lines to see:
  - What technology category they share
  - Which specific entities from each project
- **Zoom** in to see details
- **Zoom** out to see overview

## 📊 Expected Relationships

You should see **8 pink lines** total:

```
Alpha ──[3 pink lines]── Beta
  ├─ ANALYTICS
  ├─ DATABASE
  └─ SIMILAR

Alpha ──[1 pink line]── Gamma
  └─ ANALYTICS

Beta ──[4 pink lines]── Gamma
  ├─ INTEGRATION
  ├─ ANALYTICS
  ├─ CLOUD
  └─ SIMILAR (thickest line - strongest connection)
```

## 💡 If You Don't See Pink Lines

### Possible Issues:

1. **Browser cache** - Hard refresh (Ctrl+F5)
2. **Zoom level** - Try zooming out
3. **Lines overlapping** - Drag nodes apart
4. **Colors not rendering** - Try Chrome instead of Edge

### Solution:
```bash
# Regenerate the graph
python scripts/create_project_relations_graph.py

# Open in Chrome
start chrome datasets/knowledge_graphs/project_relationships_interactive.html
```

## 🎯 What Each Pink Line Means

### "DATABASE" Connection
- **Meaning**: Both projects work with database technologies
- **Alpha**: Uses SAP HANA, S/4HANA databases
- **Beta**: Uses Amazon RDS, database migration services

### "ANALYTICS" Connection
- **Meaning**: Both projects involve data/analytics
- **Appears**: Alpha ↔ Beta, Alpha ↔ Gamma, Beta ↔ Gamma
- **Most common** relationship across all projects!

### "CLOUD" Connection
- **Meaning**: Both projects use cloud technologies
- **Beta**: Cloud migration focus
- **Gamma**: Cloud-based analytics platform

### "INTEGRATION" Connection
- **Meaning**: Both projects deal with system integration
- **Beta**: AWS integration services
- **Gamma**: Continuous integration, data integration

### "SIMILAR" Connection
- **Meaning**: Very similar overall tech stacks
- **Beta ↔ Gamma**: Share 3+ technology categories (strongest!)
- **Alpha ↔ Beta**: Share 2 technology categories

## 📸 What You Should See

```
    [Alpha ERP]
         │ ╱
   PINK  │  ╱  PINK
  DATABASE│   ╱ ANALYTICS
         │    ╱
    [Beta Cloud] ━━━━━ PINK CLOUD ━━━━━ [Gamma Analytics]
                  ━━━━━ PINK SIMILAR ━━━━━
                  ━━━━━ PINK ANALYTICS ━━━━━
```

## ✅ Confirmation

Run this to confirm relationships exist:

```bash
cd datasets/knowledge_graphs
grep -o "shares_.*_tech\|similar_tech_stack" project_relationships_interactive.html | wc -l
# Should output: 8
```

## 🎁 Bonus: Both Visualizations

You have TWO interactive graphs:

1. **project_relationships_interactive.html** ⭐ **OPEN THIS!**
   - Shows PROJECT-to-PROJECT relationships clearly
   - 8 pink lines showing how projects connect
   - Cleaner, focused on projects

2. **unified_knowledge_graph_interactive.html**
   - Shows ALL entities and their relationships
   - More detailed but more complex
   - Better for entity-level exploration

---

**The project-to-project relationships ARE there!** They're the **pink/magenta lines** labeled DATABASE, CLOUD, ANALYTICS, etc. connecting the large project boxes. Open the graph and look for the PINK lines! 🎨
