"""
Component 3: ML Ranking Engine
- Loads features.csv from Component 2
- Trains a LightGBM model to score each candidate timestamp
- Outputs ranked_candidates.json with placement scores
- Generates SHAP feature importance analysis
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import shap
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FEATURES = [
    "content_score",
    "retention_at_t",
    "retention_drop_rate",
    "retention_recovery",
    "relative_position",
    "time_since_last_candidate",
]

def load_features(path="features.csv"):
    df = pd.read_csv(path)
    print(f"[Component 3] Loaded {len(df)} candidates from {path}")
    print(df[["timestamp", "type", "retention_at_t", "label"]].to_string(index=False))
    return df

def encode_type(df):
    type_map = {"silence": 0, "scene_change": 1, "transcript_boundary": 2}
    df = df.copy()
    df["type_encoded"] = df["type"].map(type_map).fillna(0).astype(int)
    return df

def train_model(df):
    df = encode_type(df)
    feature_cols = FEATURES + ["type_encoded"]
    X = df[feature_cols].fillna(0)
    y = df["label"]

    params = {
        "objective": "binary",
        "metric": "auc",
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_child_samples": 1,
        "n_estimators": 100,
        "verbose": -1,
        "random_state": 42,
    }

    n_positive = y.sum()
    n_samples = len(y)

    if n_samples >= 10 and n_positive >= 3:
        from sklearn.model_selection import StratifiedKFold
        from sklearn.metrics import roc_auc_score
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        auc_scores = []
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            m = lgb.LGBMClassifier(**params)
            m.fit(X_train, y_train, callbacks=[lgb.log_evaluation(period=-1)])
            preds = m.predict_proba(X_val)[:, 1]
            auc = roc_auc_score(y_val, preds)
            auc_scores.append(auc)
            print(f"  Fold {fold+1} AUC: {auc:.4f}")
        print(f"  Mean CV AUC: {np.mean(auc_scores):.4f}")
    else:
        print(f"  [Note] Small dataset ({n_samples} samples, {n_positive} positive)")
        print(f"  Skipping CV — training directly on all data")
        print(f"  (CV requires 10+ samples with 3+ positive labels)")

    final_model = lgb.LGBMClassifier(**params)
    final_model.fit(X, y, callbacks=[lgb.log_evaluation(period=-1)])
    print("  Final model trained ✅")
    return final_model, feature_cols

def score_candidates(df, model, feature_cols):
    df = encode_type(df)
    X = df[feature_cols].fillna(0)
    df = df.copy()
    df["placement_score"] = model.predict_proba(X)[:, 1]
    df_sorted = df.sort_values("placement_score", ascending=False).reset_index(drop=True)
    df_sorted["rank"] = df_sorted.index + 1
    mins = (df_sorted["timestamp"] // 60).astype(int)
    secs = (df_sorted["timestamp"] % 60).astype(int)
    df_sorted["timestamp_formatted"] = mins.astype(str) + "m " + secs.astype(str) + "s"
    return df_sorted

def save_shap_plot(model, df, feature_cols, output_path="shap_importance.png"):
    df = encode_type(df)
    X = df[feature_cols].fillna(0)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    vals = shap_values[1] if isinstance(shap_values, list) else shap_values
    mean_shap = np.abs(vals).mean(axis=0)
    feat_imp = pd.Series(mean_shap, index=feature_cols).sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    feat_imp.plot(kind="barh", ax=ax, color="#6C63FF")
    ax.set_title("Feature Importance (SHAP)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Mean |SHAP value|")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  SHAP plot saved → {output_path}")

def save_results(df_ranked, output_path="ranked_candidates.json"):
    results = []
    for _, row in df_ranked.iterrows():
        results.append({
            "rank": int(row["rank"]),
            "timestamp": float(row["timestamp"]),
            "timestamp_formatted": row["timestamp_formatted"],
            "type": row["type"],
            "placement_score": round(float(row["placement_score"]), 4),
            "retention_at_t": round(float(row["retention_at_t"]), 2),
            "label": int(row["label"])
        })
    with open(output_path, "w") as f:
        json.dump({"total_candidates": len(results), "ranked_placements": results}, f, indent=2)
    print(f"  Results saved → {output_path}")

def run(features_path="features.csv"):
    print("=" * 55)
    print("  COMPONENT 3: ML RANKING ENGINE")
    print("=" * 55)
    df = load_features(features_path)
    print("\n[Training LightGBM Ranker...]")
    model, feature_cols = train_model(df)
    print("\n[Scoring All Candidates...]")
    df_ranked = score_candidates(df, model, feature_cols)
    print("\n[Ranked Placement Timestamps]")
    print(df_ranked[["rank", "timestamp_formatted", "type",
                      "placement_score", "retention_at_t", "label"]].to_string(index=False))
    print("\n[Generating SHAP Feature Importance...]")
    save_shap_plot(model, df, feature_cols)
    save_results(df_ranked)
    print("\n✅ Component 3 Complete!")
    print("   → ranked_candidates.json")
    print("   → shap_importance.png")
    print("   Next: python component4_recommender.py")

if __name__ == "__main__":
    run()