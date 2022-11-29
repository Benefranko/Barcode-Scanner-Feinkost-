
fetch('/api/is_auth', {
  method: 'GET',
  credentials: 'include'
}).then(response => response.text())
   .then((response) => {
       console.log(response)
   })
   .catch(err => console.log(err));