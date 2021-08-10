from django_auth_ldap.backend import LDAPBackend

class LDAPKPIBackend(LDAPBackend):
    def authenticate_ldap_user(self, ldap_user, password):
        """ Overrides LDAPBackend.authenticate_ldap_user to save user password in django """
        user = ldap_user.authenticate(password)
        if user:
            user.extra_details.data['ldap_user'] = True
            user.extra_details.save()
            # If you set password all the time, you will logged out every another session
            if not user.check_password(password):
                user.set_password(password)
                user.save()
        #let standard AUTHENTICATION_BACKENDS make the true authentification for binding KPI and KOBOCAT
        #return user

class LDAPBackend1(LDAPKPIBackend):
    settings_prefix = "AUTH_LDAP_1_"

class LDAPBackend2(LDAPKPIBackend):
    settings_prefix = "AUTH_LDAP_2_"

class LDAPBackend3(LDAPKPIBackend):
    settings_prefix = "AUTH_LDAP_3_"
