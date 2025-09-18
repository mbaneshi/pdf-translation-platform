# Simple Authentication Plan for PDF Translation Platform

## Current State

**Problem**: Flower UI has authentication loop with Traefik basic auth
**Solution**: Temporarily disabled auth to access Flower dashboard
**Need**: Simple, working authentication that scales with future services

## Immediate Requirements

1. **Flower Access**: Secure but simple access to Celery monitoring
2. **Future Services**: Ready for Supabase and n8n integration
3. **User Management**: Basic user accounts and permissions
4. **Easy Maintenance**: Minimal operational overhead

## Simplified Solution: Authelia (Minimal Setup)

### Why Authelia (Simple Version)?
- ✅ **Works with Traefik**: No more auth loops
- ✅ **Single Container**: Just add one service to docker-compose
- ✅ **File-based Users**: No complex database setup initially
- ✅ **OAuth Ready**: Future-proof for Supabase/n8n
- ✅ **2FA Optional**: Start simple, add security later

### Architecture (Phase 1)
```
User → Traefik → Authelia → Protected Services (Flower, etc.)
```

## Implementation Plan

### Phase 1: Basic Setup (1 Week)
**Goal**: Replace broken basic auth with working Authelia

**Steps**:
1. Add Authelia container to docker-compose.yml
2. Create minimal configuration with file-based users
3. Replace Flower basic auth with Authelia middleware
4. Test and verify access works

**Result**: Working authentication for Flower

### Phase 2: Service Protection (1 Week)
**Goal**: Protect all existing services

**Steps**:
1. Add auth to PDF translation frontend
2. Create user accounts for team members
3. Set up basic access policies
4. Add 2FA for admin accounts

**Result**: All services protected with SSO

### Phase 3: Future Integration (2 Weeks)
**Goal**: Ready for Supabase and n8n

**Steps**:
1. Enable OIDC provider in Authelia
2. Migrate to database user storage
3. Create integration documentation
4. Test with sample external service

**Result**: OAuth/OIDC ready for new services

## File Structure

```
doc/
├── SIMPLE_AUTH_PLAN.md          # This overview document
├── AUTH_CURRENT_STATE.md        # Current problems and analysis
├── AUTH_EXECUTION_PHASE1.md     # Detailed Phase 1 implementation
├── AUTH_ROADMAP.md              # Long-term vision and phases
├── AUTH_CHANGELOG.md            # Implementation progress tracking
└── AUTH_TROUBLESHOOTING.md      # Common issues and solutions
```

## Success Criteria

### Phase 1 Success
- [ ] Flower accessible at https://flower.edcopo.info with Authelia auth
- [ ] No authentication loops or errors
- [ ] Admin user can login with username/password
- [ ] Session persists correctly

### Phase 2 Success
- [ ] All team members have user accounts
- [ ] PDF frontend requires authentication
- [ ] Admin panel accessible only to admin users
- [ ] 2FA enabled for sensitive accounts

### Phase 3 Success
- [ ] OAuth endpoint available for external services
- [ ] Sample integration with test application works
- [ ] User database migrated to PostgreSQL
- [ ] Ready for Supabase and n8n integration

## Resource Requirements

### Infrastructure
- **1 additional container** (Authelia)
- **Minimal RAM**: ~30MB additional usage
- **Storage**: Configuration files and user database
- **Network**: Reuse existing traefik-proxy network

### Development Time
- **Phase 1**: ~8 hours (basic setup and testing)
- **Phase 2**: ~16 hours (service integration and user management)
- **Phase 3**: ~24 hours (OIDC setup and database migration)
- **Total**: ~48 hours (~6 days)

## Risk Mitigation

### Technical Risks
- **Service Disruption**: Deploy in parallel, keep existing config as backup
- **Configuration Errors**: Start with minimal config, add features incrementally
- **Session Issues**: Use Redis for session storage (already available)

### Rollback Plan
- Keep current docker-compose.yml as backup
- Disable Authelia middleware if issues occur
- Return to no-auth state for Flower if needed

## Next Steps

1. **Review and Approve**: Confirm this simplified approach
2. **Create Phase 1 Details**: Detailed implementation guide
3. **Set Timeline**: Schedule 1-week sprint for Phase 1
4. **Prepare Environment**: Set up development/testing environment

---

*This simplified plan focuses on solving immediate authentication problems while building a foundation for future growth.*