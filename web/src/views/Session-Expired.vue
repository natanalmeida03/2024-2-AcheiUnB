<template>
  <div id="main-content" class="telaInteira bg-verde text-white p-4 min-h-screen">
    <div class="titulo flex space-x-1 mt-20 mb-16 ml-8 md:ml-0 md:flex md:justify-center md:mb-24">
      <Logo />
    </div>
    <div
      class="flex flex-col slogan max-w-72 ml-8 md:mr-8 md:max-w-none md:w-auto md:text-center mt-32"
    >
      <p class="text-5xl font-bold md:text-3xl">Sua sessão expirou.</p>
    </div>
    <div
      class="pt-[30px] px-4 lg:pt-[50px] flex flex-col items-center w-full md:w-128 mt-6 space-y-4 lg:space-y-6"
    >
      <router-link to="/" class="w-full flex justify-center">
        <button
          @click="handleLoginClick"
          class="bg-white text-verde w-full md:w-[70%] lg:w-[40%] font-semibold py-4 rounded-full hover:scale-110 transition-transform duration-300 text-center text-lg lg:text-xl"
        >
          Fazer login
        </button>
      </router-link>
    </div>
  </div>
</template>

<script setup>
function clearAllCookies() {
  const cookies = document.cookie.split(";");

  for (let cookie of cookies) {
    const eqPos = cookie.indexOf("=");
    const name = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim();
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=";
  }
}

function handleLoginClick() {
  clearAllCookies();
}
</script>
