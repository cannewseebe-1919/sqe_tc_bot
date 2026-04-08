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

    commit_message = req.commit_message or f"Add test case: {tc.title}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use GIT_ASKPASS to pass token securely (not embedded in URL)
        askpass_script = os.path.join(tmpdir, "_askpass.sh")
        with open(askpass_script, "w") as f:
            f.write(f"#!/bin/sh\necho {req.token}\n")
        os.chmod(askpass_script, 0o700)

        clone_env = os.environ.copy()
        clone_env["GIT_ASKPASS"] = askpass_script
        clone_env["GIT_TERMINAL_PROMPT"] = "0"

        clone_dir = os.path.join(tmpdir, "repo")
        try:
            repo = Repo.clone_from(
                req.repo_url, clone_dir, branch=req.branch,
                env=clone_env,
            )
        except Exception:
            repo = Repo.clone_from(req.repo_url, clone_dir, env=clone_env)
            repo.git.checkout("-b", req.branch)

        # Write TC file
        filename = f"tc_{tc.id.replace('-', '_')}.py"
        filepath = os.path.join(clone_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(tc.code)

        repo.index.add([filename])
        commit = repo.index.commit(commit_message)
        with repo.git.custom_environment(**clone_env):
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
