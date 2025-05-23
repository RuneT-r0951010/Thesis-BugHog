package main
  
import (
  "io"
  "log"
  "net/http"
  "time"
)
  
const (
  cookieName  = "session"
  contentType = "Content-Type"
  plainText   = "text/plain"
)
  
func main() {
  http.HandleFunc("/set", setCookie)
  http.HandleFunc("/clear", clearCookie)
  http.HandleFunc("/maybe-redirect", maybeRedirect)
  if err := http.ListenAndServe(":8081", nil); err != nil {
    log.Fatal(err)
  }
}
  
func setCookie(w http.ResponseWriter, r *http.Request) {
  w.Header().Set(contentType, plainText)
  cookie := http.Cookie{
    Name:     cookieName,
    Value:    "whatever",
    Path:     "/",
    Secure:   true,
    HttpOnly: true,
    SameSite: http.SameSiteLaxMode,
  }
  http.SetCookie(w, &cookie)
  io.WriteString(w, "SameSite=Lax cookie set!")
}
  
func clearCookie(w http.ResponseWriter, r *http.Request) {
  w.Header().Set(contentType, plainText)
  // clear cookie
  cookie := http.Cookie{
    Name:    cookieName,
    Expires: time.Unix(0, 0),
  }
  http.SetCookie(w, &cookie)
  io.WriteString(w, "Cookie cleared.")
}
  
func maybeRedirect(w http.ResponseWriter, r *http.Request) {
  w.Header().Set(contentType, plainText)
  for _, c := range r.Cookies() {
    if c.Name == cookieName {
      const redirectPath = "https://twitter.com/jub0bs"
      http.Redirect(w, r, redirectPath, http.StatusFound)
      return
    }
  }
  io.WriteString(w, "No cookie, no redirect...")
}