# AVA OLO Implementation Guidelines

## Core Principles

### 1. Version Control Requirements
**ALL VERSIONS MUST BE PUSHED TO GIT** - This is mandatory for:
- Audit trail and version history
- Rollback capabilities
- Team collaboration
- Automated deployments
- Production safety

### 2. Deployment Process
- **NEVER deploy directly to AWS** without Git
- All deployments must be triggered by Git push
- Use GitHub Actions for CI/CD pipeline
- Tag releases with semantic versioning

### 3. Git Workflow
```bash
# 1. Make changes
# 2. Test locally
# 3. Commit with descriptive message
git add .
git commit -m "feat: implement constitutional design system v2.5.0"

# 4. Tag the version
git tag -a v2.5.0 -m "Constitutional design system release"

# 5. Push to trigger deployment
git push origin main --tags
```

### 4. Deployment Triggers
- **Main branch push** → Deploy to production ECS
- **Git tags** → Create versioned releases
- **Pull requests** → Run tests and preview

### 5. Required Files for Git-based Deployment
- `.github/workflows/deploy-ecs.yml` - GitHub Actions workflow
- `Dockerfile` - Container definition
- `task-definition.json` - ECS task configuration
- Version in code must match Git tag

### 6. Environment Management
- **Development**: Local testing only
- **Staging**: Feature branches (optional)
- **Production**: Main branch only

### 7. Security
- Never commit secrets or passwords
- Use AWS Secrets Manager or Parameter Store
- Use GitHub Secrets for CI/CD credentials

### 8. Rollback Process
```bash
# Rollback to previous version
git checkout v2.4.0
git push origin main --force-with-lease

# Or use ECS to point to previous task definition
```

### 9. Monitoring Deployments
- Check GitHub Actions logs
- Monitor ECS service updates
- Verify health checks pass
- Test endpoints after deployment

### 10. Documentation
- Update SYSTEM_CHANGELOG.md with every release
- Document breaking changes
- Include migration guides if needed

## Example GitHub Actions Workflow

See `.github/workflows/deploy-ecs.yml` for the complete CI/CD pipeline that:
1. Builds Docker images on push
2. Pushes to ECR
3. Updates ECS task definitions
4. Deploys to ECS services
5. Monitors deployment health

## Compliance Checklist
- [ ] All code changes committed to Git
- [ ] Version tagged appropriately
- [ ] SYSTEM_CHANGELOG.md updated
- [ ] Tests pass locally
- [ ] Pushed to GitHub
- [ ] Deployment triggered automatically
- [ ] Health checks verified
- [ ] Rollback plan documented