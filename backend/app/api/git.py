import os
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from git import Repo

from app.core.auth import get_current_user
from app.models.database import get_db
from app.models.models import TestCase, GitInfo
from app.schemas.schemas import GitPushRequest, GitPushResponse

router = APIRouter(prefix="/api/git", tags=["git"])


@router.post("/push", response_model=GitPushResponse)
async def git_push(
    req: GitPushRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tc = await db.get(TestCase, req.test_case_id)
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")

    # Insert token into repo URL for auth
    repo_url = req.repo_url
    if repo_url.startswith("https://"):
        repo_url = repo_url.replace("https://", f"https://oauth2:{req.token}@")

    commit_message = req.commit_message or f"Add test case: {tc.title}"

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            repo = Repo.clone_from(repo_url, tmpdir, branch=req.branch)
        except Exception:
            repo = Repo.clone_from(repo_url, tmpdir)
            repo.git.checkout("-b", req.branch)

        # Write TC file
        filename = f"tc_{tc.id.replace('-', '_')}.py"
        filepath = os.path.join(tmpdir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(tc.code)

        repo.index.add([filename])
        commit = repo.index.commit(commit_message)
        repo.remote("origin").push(req.branch)

        # Update DB
        git_info = GitInfo(
            test_case_id=tc.id,
            repo_url=req.repo_url,
            branch=req.branch,
            commit_message=commit_message,
            pushed_at=datetime.now(timezone.utc),
            pushed_by=user["sub"],
        )
        db.add(git_info)
        tc.status = "pushed"
        await db.commit()

        return GitPushResponse(
            success=True,
            commit_sha=str(commit.hexsha),
            message=f"Pushed {filename} to {req.branch}",
        )
