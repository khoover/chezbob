# profile.pl
#
# Routines and variables which support user profiles.  To add a
# new property to the user profile, simply add a field to the PROFILE
# array that contains a name for the property.  Also add a description of
# the property in the DESC array.  After that you can start populating the
# rest of the code with references to the PROFILE array.  For example,
# I could check if the speech property is enabled as follows:
#
#    if ($PROFILE{"Speech"}) {  # say something }
#
# We currently use dialog's 'checklist' window for displaying user 
# profiles.  This restricts us from having any non-binary (on/off) profile 
# properties.  The code in this file, however, does not make this 
# assumption, so if we upgraded to a more flexible widget package, it
# would be possible to have more complex properties. 
#
# New users of the system automatically have every property of their 
# profile turned 'off'.  
#
# $Id: profile.pl,v 1.6 2001-05-22 03:29:31 mcopenha Exp $
#

require "bob_db.pl";
require "dlg.pl";

%PROFILE = (
  "Auto Logout", -1,
  "No Confirmation", -1,
  "Speech", -1
);

%DESC = (
  "Auto Logout", "Automatically log me out after a purchase",
  "No Confirmation", "Do not ask me to confirm a purchase",
  "Speech", "Verbally greet me and confirm purchases"
); 


sub
get_user_profile
#
# Retrieve the user profile of 'userid' and store it in the global 
# associative array 'PROFILE'.  Should be called once every time a 
# different user logs in.
#
{
  my ($userid) = @_;
  foreach $property (keys %PROFILE) { 
    my $dbsetting = &bob_db_get_profile_setting($userid, $property);
    if ($dbsetting == $NOT_FOUND) {
      &bob_db_insert_property($userid, $property);
      $PROFILE{$property} = 0;
    } else {
      $PROFILE{$property} = $dbsetting;
    }
  }
}


sub
profile_win
#
# Display the user profile of 'userid' in a checklist window.  Save 
# alterations to the database.
#
{
  my ($userid) = @_;
  my $win_title = "My Chez Bob";
  my $win_text = q{
Change any of the following properties:};

  my $profile_menu = "";

  foreach $property (keys %PROFILE) {
    $profile_menu .= "\"" . $property . "\" ";
    $profile_menu .= "\"" . $DESC{$property} . "\" ";
    $profile_menu .= $PROFILE{$property} ? "on " : "off ";
  }   
  
  if (system("$DLG --title \"$win_title\" --clear --cr-wrap --checklist \" " .
    $win_text .  "\" 13 70 5 $profile_menu 2> $TMP/input.profile") != 0) {
    return;
  }

  # Strip quotes from beginning and end
  my $tmpstr = `cat $TMP/input.profile`;
  $tmpstr =~ s/^\"//;
  $tmpstr =~ s/(\"\s*)$//;

  my @selected = ();
  @selected = split(/\" \"/, $tmpstr);
  foreach $property (keys %PROFILE) {
    $PROFILE{$property} = 0;
  }
  foreach $property (@selected) {
    $PROFILE{$property} = 1;
  }

  &bob_db_update_profile_settings($userid, %PROFILE);
}

1;
